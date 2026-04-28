"""Service for audio effects processing."""
from __future__ import annotations

import uuid
from datetime import datetime, UTC
from sqlalchemy.orm import Session
from app.models.ai_effects import AudioEffect, UserAudioEffectPreset
from app.models.audio_job import AudioJob
from app.repositories.job_repo import JobRepository
from app.repositories.credit_repo import CreditRepository


class AudioEffectsService:
    """Manage audio effects and effect presets."""

    def __init__(self, db: Session):
        self.db = db
        self.jobs = JobRepository(db)
        self.credits = CreditRepository(db)

    def get_all_effects(self) -> list[AudioEffect]:
        """Get all available audio effects."""
        return self.db.query(AudioEffect).all()

    def get_effect_by_type(self, effect_type: str) -> AudioEffect | None:
        """Get effect by type."""
        return self.db.query(AudioEffect).filter_by(effect_type=effect_type).first()

    def create_user_preset(
        self,
        user_id: uuid.UUID,
        effect_id: uuid.UUID,
        preset_name: str,
        parameters: dict,
        is_public: bool = False
    ) -> UserAudioEffectPreset:
        """Create a new user effect preset."""
        preset = UserAudioEffectPreset(
            user_id=user_id,
            effect_id=effect_id,
            preset_name=preset_name,
            parameters=parameters,
            is_public=is_public
        )
        self.db.add(preset)
        self.db.commit()
        self.db.refresh(preset)
        return preset

    def get_user_presets(self, user_id: uuid.UUID) -> list[UserAudioEffectPreset]:
        """Get all presets for a user."""
        return self.db.query(UserAudioEffectPreset).filter_by(user_id=user_id).all()

    def delete_preset(self, preset_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Delete a user preset. Returns True if deleted, False if not found, raises on ownership mismatch."""
        preset = self.db.query(UserAudioEffectPreset).filter_by(id=preset_id).first()
        if not preset:
            return False
        if preset.user_id != user_id:
            raise PermissionError('Preset belongs to a different user')
        self.db.delete(preset)
        self.db.commit()
        return True

    def apply_effect(
        self,
        user_id: uuid.UUID,
        effect_type: str,
        parameters: dict,
        input_file_key: str,
        idempotency_key: str | None = None
    ) -> AudioJob:
        """Create a job to apply audio effect to a file.
        
        Cost: 100 credits for any effect application.
        """
        # Reserve credits
        if not self.credits.has_sufficient_balance(user_id, 100):
            raise ValueError("Insufficient credits to apply effect")

        job_data = {
            'effect_type': effect_type,
            'parameters': parameters,
            'input_file_key': input_file_key,
        }

        job, created = self.jobs.create_or_get(
            user_id=user_id,
            job_type='audio_effect',
            request_json=job_data,
            idempotency_key=idempotency_key,
            expected_credits=100
        )

        if created:
            self.credits.reserve_credits(user_id, 100, job.id)

            from app.workers.audio_tasks import enqueue_audio_effect_job  # avoid circular at module level
            enqueue_audio_effect_job(str(job.id))
        return job

    def initialize_default_effects(self) -> None:
        """Initialize default audio effects in the database."""
        effects = [
            {
                'name': 'Echo - Short Delay',
                'effect_type': 'echo',
                'description': 'Add a short echo effect with controllable delay and feedback.',
                'default_params': {'delay_ms': 250, 'feedback_ratio': 0.5}
            },
            {
                'name': 'Echo - Long Delay',
                'effect_type': 'echo',
                'description': 'Add a long echo effect with extended delay.',
                'default_params': {'delay_ms': 500, 'feedback_ratio': 0.3}
            },
            {
                'name': 'Reverb - Small Room',
                'effect_type': 'reverb',
                'description': 'Simulate a small room acoustic environment.',
                'default_params': {'room_size': 0.3, 'wet': 0.3}
            },
            {
                'name': 'Reverb - Large Hall',
                'effect_type': 'reverb',
                'description': 'Simulate a large concert hall acoustic environment.',
                'default_params': {'room_size': 0.8, 'wet': 0.5}
            },
            {
                'name': 'EQ - Boost Bass',
                'effect_type': 'eq',
                'description': 'Boost low frequencies for a warmer sound.',
                'default_params': {'bass_db': 6.0, 'mid_db': 0.0, 'treble_db': 0.0}
            },
            {
                'name': 'EQ - Bright Treble',
                'effect_type': 'eq',
                'description': 'Boost high frequencies for clarity.',
                'default_params': {'bass_db': 0.0, 'mid_db': 0.0, 'treble_db': 6.0}
            },
            {
                'name': 'EQ - Warm Mid',
                'effect_type': 'eq',
                'description': 'Boost mid frequencies for warmth.',
                'default_params': {'bass_db': 3.0, 'mid_db': 4.0, 'treble_db': 2.0}
            },
        ]

        for effect_data in effects:
            existing = self.db.query(AudioEffect).filter_by(effect_type=effect_data['effect_type']).first()
            if not existing:
                effect = AudioEffect(
                    name=effect_data['name'],
                    effect_type=effect_data['effect_type'],
                    description=effect_data['description'],
                    default_params=effect_data['default_params'],
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC)
                )
                self.db.add(effect)

        self.db.commit()
