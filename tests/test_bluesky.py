from social_autoposter.adapters.bluesky import BlueskyAdapter
from social_autoposter.adapters.mastodon import MastodonAdapter
from social_autoposter.adapters.linkedin import LinkedInAdapter
from social_autoposter.models import Content


def test_bluesky_dry_run_does_not_make_request():
    class ForbiddenSession:
        def request(self, *args, **kwargs):
            raise AssertionError("dry-run must not make network requests")

    result = BlueskyAdapter("me.bsky.social", "secret", dry_run=True, session=ForbiddenSession()).post(
        Content("1", "agency", "Hello", link="https://example.com")
    )
    assert result.success is True
    assert result.dry_run is True
    assert result.post_id == "dry-run:1"


def test_mastodon_dry_run_does_not_require_credentials():
    result = MastodonAdapter("", "", dry_run=True).post(Content("2", "agency", "Hello Mastodon"))
    assert result.success is True
    assert result.dry_run is True


def test_linkedin_dry_run_does_not_require_credentials():
    result = LinkedInAdapter(dry_run=True).post(Content("3", "agency", "Hello LinkedIn"))
    assert result.success is True
    assert result.dry_run is True
