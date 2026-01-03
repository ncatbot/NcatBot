"""Tests for ncatbot.core.helper.forward_constructor module."""

import pytest


class TestForwardConstructorInit:
    """Tests for ForwardConstructor initialization."""

    def test_init_default_values(self):
        """Test default initialization values."""
        from ncatbot.core.helper.forward_constructor import ForwardConstructor

        fc = ForwardConstructor()
        assert fc.user_id == "123456"
        assert fc.nickname == "QQ用户"
        assert fc.content == []

    def test_init_custom_values(self):
        """Test initialization with custom values."""
        from ncatbot.core.helper.forward_constructor import ForwardConstructor

        fc = ForwardConstructor(user_id="999999", nickname="CustomUser")
        assert fc.user_id == "999999"
        assert fc.nickname == "CustomUser"

    def test_init_with_content(self):
        """Test initialization with pre-existing content."""
        from ncatbot.core.helper.forward_constructor import ForwardConstructor
        from ncatbot.core.event import Node, MessageArray, Text

        node = Node(user_id="111", nickname="Test", content=MessageArray(Text("Hello")))
        fc = ForwardConstructor(content=[node])

        assert len(fc.content) == 1


class TestForwardConstructorSetAuthor:
    """Tests for set_author method."""

    def test_set_author(self):
        """Test setting author information."""
        from ncatbot.core.helper.forward_constructor import ForwardConstructor

        fc = ForwardConstructor()
        fc.set_author("888888", "NewUser")

        assert fc.user_id == "888888"
        assert fc.nickname == "NewUser"


class TestForwardConstructorAttach:
    """Tests for attach methods."""

    def test_attach_message_array(self):
        """Test attaching a MessageArray."""
        from ncatbot.core.helper.forward_constructor import ForwardConstructor
        from ncatbot.core.event import MessageArray, Text

        fc = ForwardConstructor()
        content = MessageArray(Text("Hello"))
        fc.attach(content)

        assert len(fc.content) == 1
        assert fc.content[0].user_id == "123456"
        assert fc.content[0].nickname == "QQ用户"

    def test_attach_with_custom_author(self):
        """Test attaching with custom author."""
        from ncatbot.core.helper.forward_constructor import ForwardConstructor
        from ncatbot.core.event import MessageArray, Text

        fc = ForwardConstructor()
        content = MessageArray(Text("Hello"))
        fc.attach(content, user_id="777777", nickname="SpecialUser")

        assert fc.content[0].user_id == "777777"
        assert fc.content[0].nickname == "SpecialUser"

    def test_attach_message(self):
        """Test attach_message method."""
        from ncatbot.core.helper.forward_constructor import ForwardConstructor
        from ncatbot.core.event import MessageArray, Text

        fc = ForwardConstructor()
        fc.attach_message(MessageArray(Text("Test message")))

        assert len(fc.content) == 1

    def test_attach_text(self):
        """Test attach_text method."""
        from ncatbot.core.helper.forward_constructor import ForwardConstructor

        fc = ForwardConstructor()
        fc.attach_text("Simple text message")

        assert len(fc.content) == 1

    def test_attach_text_with_author(self):
        """Test attach_text with custom author."""
        from ncatbot.core.helper.forward_constructor import ForwardConstructor

        fc = ForwardConstructor()
        fc.attach_text("Text", user_id="555555", nickname="TextAuthor")

        assert fc.content[0].user_id == "555555"
        assert fc.content[0].nickname == "TextAuthor"

    def test_attach_image(self):
        """Test attach_image method."""
        from ncatbot.core.helper.forward_constructor import ForwardConstructor

        fc = ForwardConstructor()
        fc.attach_image("http://example.com/image.png")

        assert len(fc.content) == 1

    def test_attach_file(self):
        """Test attach_file method."""
        from ncatbot.core.helper.forward_constructor import ForwardConstructor

        fc = ForwardConstructor()
        fc.attach_file("/path/to/file.txt")

        assert len(fc.content) == 1

    def test_attach_video(self):
        """Test attach_video method."""
        from ncatbot.core.helper.forward_constructor import ForwardConstructor

        fc = ForwardConstructor()
        fc.attach_video("/path/to/video.mp4")

        assert len(fc.content) == 1


class TestForwardConstructorAttachForward:
    """Tests for attach_forward method."""

    def test_attach_forward(self):
        """Test attaching a Forward object."""
        from ncatbot.core.helper.forward_constructor import ForwardConstructor
        from ncatbot.core.event import Forward, Node, MessageArray, Text

        fc = ForwardConstructor()
        nested_forward = Forward(
            content=[
                Node(
                    user_id="111",
                    nickname="Inner",
                    content=MessageArray(Text("Nested")),
                )
            ]
        )
        fc.attach_forward(nested_forward)

        assert len(fc.content) == 1

    def test_attach_forward_empty_content_raises(self):
        """Test that attaching Forward with empty content raises ValueError."""
        from ncatbot.core.helper.forward_constructor import ForwardConstructor
        from ncatbot.core.event import Forward

        fc = ForwardConstructor()
        empty_forward = Forward(content=None)

        with pytest.raises(ValueError, match="content 不能为空"):
            fc.attach_forward(empty_forward)


class TestForwardConstructorToForward:
    """Tests for to_forward method."""

    def test_to_forward_empty(self):
        """Test converting empty constructor to Forward."""
        from ncatbot.core.helper.forward_constructor import ForwardConstructor
        from ncatbot.core.event import Forward

        fc = ForwardConstructor()
        forward = fc.to_forward()

        assert isinstance(forward, Forward)
        assert forward.content == []

    def test_to_forward_with_content(self):
        """Test converting constructor with content to Forward."""
        from ncatbot.core.helper.forward_constructor import ForwardConstructor
        from ncatbot.core.event import Forward

        fc = ForwardConstructor()
        fc.attach_text("Message 1")
        fc.attach_text("Message 2")
        fc.attach_text("Message 3")

        forward = fc.to_forward()

        assert isinstance(forward, Forward)
        assert len(forward.content) == 3


class TestForwardConstructorMultipleMessages:
    """Tests for building complex forward messages."""

    def test_multiple_messages_different_authors(self):
        """Test building forward with multiple authors."""
        from ncatbot.core.helper.forward_constructor import ForwardConstructor

        fc = ForwardConstructor()

        fc.set_author("111111", "User1")
        fc.attach_text("Hello from User1")

        fc.set_author("222222", "User2")
        fc.attach_text("Hello from User2")

        fc.attach_text("Another message", user_id="333333", nickname="User3")

        assert len(fc.content) == 3
        assert fc.content[0].user_id == "111111"
        assert fc.content[1].user_id == "222222"
        assert fc.content[2].user_id == "333333"

    def test_mixed_content_types(self):
        """Test building forward with mixed content types."""
        from ncatbot.core.helper.forward_constructor import ForwardConstructor

        fc = ForwardConstructor()

        fc.attach_text("Text message")
        fc.attach_image("http://example.com/image.png")
        fc.attach_file("/path/to/file.txt")
        fc.attach_video("/path/to/video.mp4")

        assert len(fc.content) == 4

    def test_chained_operations(self):
        """Test chained operations work correctly."""
        from ncatbot.core.helper.forward_constructor import ForwardConstructor

        fc = ForwardConstructor(user_id="000000", nickname="Bot")

        # Set author and add multiple messages
        fc.set_author("111111", "User1")
        fc.attach_text("Message 1")
        fc.attach_text("Message 2")

        fc.set_author("222222", "User2")
        fc.attach_text("Message 3")

        forward = fc.to_forward()

        assert len(forward.content) == 3
        # First two messages should use User1
        assert forward.content[0].user_id == "111111"
        assert forward.content[1].user_id == "111111"
        # Third message should use User2
        assert forward.content[2].user_id == "222222"
