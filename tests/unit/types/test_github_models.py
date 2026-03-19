"""
GitHub 类型模型测试 — GitHubModel 基类 + API 响应模型

规范:
  GHM-01: GitHubModel 继承 BaseModel，支持 extra="allow"
  GHM-02: GitHubModel dict 兼容层（下标访问 / get / in）
  GHM-03: 事件内嵌模型迁移到 GitHubModel 后行为不变
  GHM-04: GitHubUserInfo model_validate 正常工作
  GHM-05: GitHubIssueInfo 含嵌套 user / labels / assignees
  GHM-06: GitHubCommentInfo model_validate 正常工作
  GHM-07: GitHubPullRequestInfo 含嵌套 head / base / user
  GHM-08: GitHubMergeResult model_validate 正常工作
  GHM-09: GitHubReleaseInfo 继承 GitHubRelease 并扩展
  GHM-10: GitHubRepoInfo 含嵌套 owner
  GHM-11: GitHubLabelInfo model_validate 正常工作
  GHM-12: Attachment model 及字段
  GHM-13: AttachmentKind 枚举 + Attachment 子类
  GHM-14: AttachmentList 过滤方法
  GHM-15: Attachment.to_segment() 返回正确段类型
"""

from __future__ import annotations

import pytest

from ncatbot.types.github._base import GitHubModel
from ncatbot.types.github.models import (
    GitHubCommentInfo,
    GitHubCommit,
    GitHubForkee,
    GitHubIssueInfo,
    GitHubLabelInfo,
    GitHubMergeResult,
    GitHubPullRequestInfo,
    GitHubRelease,
    GitHubReleaseAsset,
    GitHubReleaseInfo,
    GitHubRepo,
    GitHubRepoInfo,
    GitHubUserInfo,
)
from ncatbot.types.common.attachment import (
    Attachment,
    AttachmentKind,
    AudioAttachment,
    FileAttachment,
    ImageAttachment,
    VideoAttachment,
)
from ncatbot.types.common.attachment_list import AttachmentList


# ---- GHM-01: GitHubModel extra="allow" ----


class TestGitHubModelBase:
    def test_ghm01_extra_fields_allowed(self):
        """GHM-01: GitHubModel 允许未声明字段"""
        user = GitHubUserInfo.model_validate(
            {"login": "octocat", "id": 1, "node_id": "MDQ6VXNlcjE="}
        )
        assert user.login == "octocat"
        assert user.node_id == "MDQ6VXNlcjE="  # type: ignore[attr-defined]

    def test_ghm02_dict_compat_getitem(self):
        """GHM-02: 下标访问"""
        user = GitHubUserInfo(login="octocat", id=1)
        assert user["login"] == "octocat"
        with pytest.raises(KeyError):
            user["nonexistent"]

    def test_ghm02_dict_compat_get(self):
        """GHM-02: get 方法"""
        user = GitHubUserInfo(login="octocat", id=1)
        assert user.get("login") == "octocat"
        assert user.get("nonexistent", "fallback") == "fallback"

    def test_ghm02_dict_compat_contains(self):
        """GHM-02: in 操作符"""
        user = GitHubUserInfo(login="octocat", id=1)
        assert "login" in user
        assert "nonexistent" not in user


# ---- GHM-03: 事件内嵌模型迁移无回归 ----


class TestEventEmbeddedModels:
    def test_ghm03_github_repo(self):
        """GHM-03: GitHubRepo 迁移后行为不变"""
        repo = GitHubRepo(owner="ncatbot", name="NcatBot", full_name="ncatbot/NcatBot")
        assert repo.full_name == "ncatbot/NcatBot"
        assert isinstance(repo, GitHubModel)

    def test_ghm03_github_release_asset_coerce(self):
        """GHM-03: GitHubReleaseAsset id 从 int 转 str（coerce_numbers_to_str）"""
        asset = GitHubReleaseAsset.model_validate(
            {"id": 42, "name": "a.zip", "size": 1024}
        )
        assert asset.id == "42"
        assert isinstance(asset, GitHubModel)

    def test_ghm03_github_commit(self):
        repo = GitHubCommit(sha="abc123", message="fix")
        assert repo.sha == "abc123"

    def test_ghm03_github_forkee(self):
        forkee = GitHubForkee(full_name="user/fork", owner="user")
        assert forkee.owner == "user"


# ---- GHM-04 ~ GHM-11: API 响应模型 ----


class TestAPIResponseModels:
    def test_ghm04_user_info(self):
        """GHM-04: GitHubUserInfo"""
        raw = {
            "login": "octocat",
            "id": 1,
            "avatar_url": "https://avatars.githubusercontent.com/u/1?v=4",
            "html_url": "https://github.com/octocat",
            "type": "User",
            "name": "The Octocat",
            "bio": "GitHub mascot",
            "public_repos": 10,
        }
        user = GitHubUserInfo.model_validate(raw)
        assert user.login == "octocat"
        assert user.public_repos == 10
        assert user.type == "User"

    def test_ghm05_issue_info_nested(self):
        """GHM-05: GitHubIssueInfo 含嵌套 user/labels/assignees"""
        raw = {
            "id": 100,
            "number": 42,
            "title": "Bug report",
            "body": "Something broken",
            "state": "open",
            "html_url": "https://github.com/owner/repo/issues/42",
            "user": {"login": "reporter", "id": 2},
            "labels": [
                {"id": 1, "name": "bug", "color": "d73a4a"},
                {"id": 2, "name": "help wanted", "color": "008672"},
            ],
            "assignees": [{"login": "dev", "id": 3}],
            "comments": 5,
            "created_at": "2026-01-01T00:00:00Z",
        }
        issue = GitHubIssueInfo.model_validate(raw)
        assert issue.number == 42
        assert issue.user.login == "reporter"
        assert len(issue.labels) == 2
        assert issue.labels[0].name == "bug"
        assert issue.assignees[0].login == "dev"

    def test_ghm06_comment_info(self):
        """GHM-06: GitHubCommentInfo"""
        raw = {
            "id": 200,
            "body": "Great work!",
            "user": {"login": "reviewer", "id": 5},
            "html_url": "https://github.com/owner/repo/issues/42#issuecomment-200",
            "created_at": "2026-01-01T00:00:00Z",
        }
        comment = GitHubCommentInfo.model_validate(raw)
        assert comment.body == "Great work!"
        assert comment.user.login == "reviewer"

    def test_ghm07_pr_info_nested(self):
        """GHM-07: GitHubPullRequestInfo 含嵌套 head/base/user"""
        raw = {
            "id": 300,
            "number": 10,
            "title": "Feature PR",
            "state": "open",
            "head": {"ref": "feature", "sha": "abc123", "label": "user:feature"},
            "base": {"ref": "main", "sha": "def456", "label": "owner:main"},
            "user": {"login": "contributor", "id": 7},
            "merged": False,
            "draft": False,
        }
        pr = GitHubPullRequestInfo.model_validate(raw)
        assert pr.number == 10
        assert pr.head.ref == "feature"
        assert pr.base.ref == "main"
        assert pr.user.login == "contributor"

    def test_ghm08_merge_result(self):
        """GHM-08: GitHubMergeResult"""
        raw = {
            "sha": "abc123def",
            "merged": True,
            "message": "Pull Request successfully merged",
        }
        result = GitHubMergeResult.model_validate(raw)
        assert result.merged is True
        assert result.sha == "abc123def"

    def test_ghm09_release_info_extends_release(self):
        """GHM-09: GitHubReleaseInfo 继承 GitHubRelease"""
        raw = {
            "id": "500",
            "tag_name": "v2.0.0",
            "name": "v2.0.0",
            "body": "Release notes",
            "prerelease": False,
            "draft": False,
            "html_url": "https://github.com/owner/repo/releases/tag/v2.0.0",
            "author": {"login": "maintainer", "id": 10},
            "assets": [
                {
                    "id": 1,
                    "name": "binary.zip",
                    "size": 2048,
                    "browser_download_url": "https://example.com/dl",
                },
            ],
            "created_at": "2026-01-01T00:00:00Z",
            "published_at": "2026-01-01T12:00:00Z",
            "tarball_url": "https://api.github.com/repos/owner/repo/tarball/v2.0.0",
            "zipball_url": "https://api.github.com/repos/owner/repo/zipball/v2.0.0",
        }
        info = GitHubReleaseInfo.model_validate(raw)
        assert isinstance(info, GitHubRelease)
        assert info.tag_name == "v2.0.0"
        assert info.author.login == "maintainer"
        assert len(info.assets) == 1
        assert info.assets[0].name == "binary.zip"
        assert info.tarball_url is not None

    def test_ghm10_repo_info_nested(self):
        """GHM-10: GitHubRepoInfo 含嵌套 owner"""
        raw = {
            "id": 600,
            "name": "NcatBot",
            "full_name": "ncatbot/NcatBot",
            "owner": {"login": "ncatbot", "id": 20},
            "private": False,
            "html_url": "https://github.com/ncatbot/NcatBot",
            "description": "Bot framework",
            "fork": False,
            "default_branch": "main",
            "language": "Python",
            "stargazers_count": 100,
            "forks_count": 25,
            "open_issues_count": 10,
        }
        repo = GitHubRepoInfo.model_validate(raw)
        assert repo.full_name == "ncatbot/NcatBot"
        assert repo.owner.login == "ncatbot"
        assert repo.language == "Python"
        assert repo.stargazers_count == 100

    def test_ghm11_label_info(self):
        """GHM-11: GitHubLabelInfo"""
        raw = {
            "id": 1,
            "name": "bug",
            "color": "d73a4a",
            "description": "Something isn't working",
        }
        label = GitHubLabelInfo.model_validate(raw)
        assert label.name == "bug"
        assert label.color == "d73a4a"


# ---- GHM-12: Attachment ----


class TestAttachment:
    def test_ghm12_attachment_fields(self):
        """GHM-12: Attachment 基本字段"""
        att = Attachment(
            name="release.zip",
            url="https://example.com/dl",
            size=4096,
            content_type="application/zip",
            extra={"id": "42"},
        )
        assert att.name == "release.zip"
        assert att.url == "https://example.com/dl"
        assert att.size == 4096
        assert att.extra["id"] == "42"
        assert att.kind == AttachmentKind.OTHER

    def test_ghm12_attachment_defaults(self):
        """GHM-12: Attachment 可选字段默认值"""
        att = Attachment(name="file.txt", url="https://example.com/f")
        assert att.size is None
        assert att.content_type is None
        assert att.kind == AttachmentKind.OTHER


# ---- GHM-13: AttachmentKind + 子类 ----


class TestAttachmentSubclasses:
    def test_ghm13_image_attachment(self):
        """GHM-13: ImageAttachment 带 kind=IMAGE + width/height"""
        att = ImageAttachment(
            name="photo.jpg",
            url="https://example.com/photo.jpg",
            size=2048,
            width=1920,
            height=1080,
        )
        assert att.kind == AttachmentKind.IMAGE
        assert isinstance(att, Attachment)
        assert att.width == 1920
        assert att.height == 1080

    def test_ghm13_video_attachment(self):
        """GHM-13: VideoAttachment 带 kind=VIDEO + duration"""
        att = VideoAttachment(
            name="clip.mp4",
            url="https://example.com/clip.mp4",
            duration=120,
        )
        assert att.kind == AttachmentKind.VIDEO
        assert isinstance(att, Attachment)
        assert att.duration == 120

    def test_ghm13_audio_attachment(self):
        """GHM-13: AudioAttachment 带 kind=AUDIO + duration"""
        att = AudioAttachment(
            name="voice.ogg",
            url="https://example.com/voice.ogg",
            duration=30,
        )
        assert att.kind == AttachmentKind.AUDIO
        assert att.duration == 30

    def test_ghm13_file_attachment(self):
        """GHM-13: FileAttachment 带 kind=FILE"""
        att = FileAttachment(
            name="data.csv",
            url="https://example.com/data.csv",
            size=512,
        )
        assert att.kind == AttachmentKind.FILE

    def test_ghm13_kind_enum_values(self):
        """GHM-13: AttachmentKind 枚举值"""
        assert AttachmentKind.IMAGE == "image"
        assert AttachmentKind.VIDEO == "video"
        assert AttachmentKind.AUDIO == "audio"
        assert AttachmentKind.FILE == "file"
        assert AttachmentKind.OTHER == "other"


# ---- GHM-14: AttachmentList 过滤 ----


class TestAttachmentList:
    @pytest.fixture()
    def mixed_list(self) -> AttachmentList:
        return AttachmentList(
            [
                ImageAttachment(name="a.jpg", url="http://a", size=100),
                ImageAttachment(name="b.png", url="http://b", size=200),
                VideoAttachment(name="c.mp4", url="http://c", size=5000),
                AudioAttachment(name="d.ogg", url="http://d", size=50),
                FileAttachment(name="e.zip", url="http://e", size=3000),
                Attachment(name="f.dat", url="http://f", size=10),
            ]
        )

    def test_ghm14_images(self, mixed_list):
        """GHM-14: images() 只返回 ImageAttachment"""
        imgs = mixed_list.images()
        assert len(imgs) == 2
        assert isinstance(imgs, AttachmentList)
        assert all(isinstance(a, ImageAttachment) for a in imgs)

    def test_ghm14_videos(self, mixed_list):
        """GHM-14: videos() 只返回 VideoAttachment"""
        assert len(mixed_list.videos()) == 1

    def test_ghm14_audios(self, mixed_list):
        """GHM-14: audios() 只返回 AudioAttachment"""
        assert len(mixed_list.audios()) == 1

    def test_ghm14_files(self, mixed_list):
        """GHM-14: files() 只返回 FileAttachment"""
        assert len(mixed_list.files()) == 1

    def test_ghm14_by_kind(self, mixed_list):
        """GHM-14: by_kind() 多种类型过滤"""
        result = mixed_list.by_kind(AttachmentKind.IMAGE, AttachmentKind.VIDEO)
        assert len(result) == 3

    def test_ghm14_by_content_type(self):
        """GHM-14: by_content_type() 用 glob 过滤"""
        al = AttachmentList(
            [
                ImageAttachment(
                    name="x.jpg", url="http://x", content_type="image/jpeg"
                ),
                VideoAttachment(name="y.mp4", url="http://y", content_type="video/mp4"),
            ]
        )
        assert len(al.by_content_type("image/*")) == 1

    def test_ghm14_first(self, mixed_list):
        """GHM-14: first() 返回第一个"""
        assert mixed_list.first().name == "a.jpg"
        assert AttachmentList().first() is None

    def test_ghm14_largest(self, mixed_list):
        """GHM-14: largest() 返回 size 最大的"""
        assert mixed_list.largest().name == "c.mp4"

    def test_ghm14_smallest(self, mixed_list):
        """GHM-14: smallest() 返回 size 最小的"""
        assert mixed_list.smallest().name == "f.dat"

    def test_ghm14_is_list(self, mixed_list):
        """GHM-14: AttachmentList 是 list 的子类"""
        assert isinstance(mixed_list, list)
        assert len(mixed_list) == 6


# ---- GHM-15: to_segment() ----


class TestToSegment:
    def test_ghm15_image_to_segment(self):
        """GHM-15: ImageAttachment.to_segment() 返回 Image 段"""
        from ncatbot.types.common.segment.media import Image

        att = ImageAttachment(name="x.jpg", url="http://example.com/x.jpg", size=100)
        seg = att.to_segment()
        assert isinstance(seg, Image)
        assert seg.file == "http://example.com/x.jpg"

    def test_ghm15_video_to_segment(self):
        """GHM-15: VideoAttachment.to_segment() 返回 Video 段"""
        from ncatbot.types.common.segment.media import Video

        att = VideoAttachment(name="v.mp4", url="http://example.com/v.mp4")
        seg = att.to_segment()
        assert isinstance(seg, Video)

    def test_ghm15_audio_to_segment(self):
        """GHM-15: AudioAttachment.to_segment() 返回 Record 段"""
        from ncatbot.types.common.segment.media import Record

        att = AudioAttachment(name="a.ogg", url="http://example.com/a.ogg")
        seg = att.to_segment()
        assert isinstance(seg, Record)

    def test_ghm15_file_to_segment(self):
        """GHM-15: FileAttachment.to_segment() 返回 File 段"""
        from ncatbot.types.common.segment.media import File

        att = FileAttachment(name="f.zip", url="http://example.com/f.zip")
        seg = att.to_segment()
        assert isinstance(seg, File)

    def test_ghm15_base_attachment_to_segment(self):
        """GHM-15: Attachment 基类 to_segment() 返回 File 段"""
        from ncatbot.types.common.segment.media import File

        att = Attachment(name="f.dat", url="http://example.com/f.dat")
        seg = att.to_segment()
        assert isinstance(seg, File)
        assert att.extra == {}
