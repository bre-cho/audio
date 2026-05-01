from app.services.podcast_episode_builder import PodcastEpisodeBuilder


def test_podcast_episode_plan_segments():
    plan = PodcastEpisodeBuilder().build_plan(title="Demo", script="Host: Hello\nGuest: Hi", speakers=["Host", "Guest"])
    data = plan.dict()
    assert data["title"] == "Demo"
    assert len(data["segments"]) == 2
    assert data["segments"][0]["speaker"] == "Host"
