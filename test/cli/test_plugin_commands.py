"""插件命令单元测试"""

from unittest.mock import patch


class TestCreatePluginTemplate:
    """create_plugin_template 命令测试"""

    def test_create_plugin_basic(self, mock_config, temp_plugins_dir, capsys):
        """测试创建基本插件模板"""
        with patch("ncatbot.cli.commands.plugin_commands.config", mock_config):
            from ncatbot.cli.commands.plugin_commands import create_plugin_template

            create_plugin_template(
                "test_plugin", author="TestAuthor", non_interactive=True
            )

            plugin_dir = temp_plugins_dir / "test_plugin"
            assert plugin_dir.exists()
            assert (plugin_dir / "manifest.toml").exists()
            assert (plugin_dir / "plugin.py").exists()
            assert (plugin_dir / "__init__.py").exists()

            captured = capsys.readouterr()
            assert "创建成功" in captured.out

    def test_create_plugin_manifest_content(self, mock_config, temp_plugins_dir):
        """测试插件 manifest 内容"""
        with patch("ncatbot.cli.commands.plugin_commands.config", mock_config):
            from ncatbot.cli.commands.plugin_commands import create_plugin_template

            create_plugin_template("my_plugin", author="John", non_interactive=True)

            manifest = (temp_plugins_dir / "my_plugin" / "manifest.toml").read_text(
                encoding="utf-8"
            )
            assert 'name = "my_plugin"' in manifest
            assert 'author = "John"' in manifest

    def test_create_plugin_invalid_name(self, mock_config, capsys):
        """测试无效插件名"""
        with patch("ncatbot.cli.commands.plugin_commands.config", mock_config):
            from ncatbot.cli.commands.plugin_commands import create_plugin_template

            create_plugin_template("123invalid", non_interactive=True)

            captured = capsys.readouterr()
            assert "不合法" in captured.out

    def test_create_plugin_name_with_underscore(self, mock_config, temp_plugins_dir):
        """测试带下划线的插件名"""
        with patch("ncatbot.cli.commands.plugin_commands.config", mock_config):
            from ncatbot.cli.commands.plugin_commands import create_plugin_template

            create_plugin_template("my_cool_plugin", non_interactive=True)

            assert (temp_plugins_dir / "my_cool_plugin").exists()

    def test_create_plugin_overwrite_cancel(
        self, mock_config, temp_plugins_dir, capsys
    ):
        """测试覆盖取消"""
        # 先创建一个插件
        (temp_plugins_dir / "existing").mkdir()

        with (
            patch("ncatbot.cli.commands.plugin_commands.config", mock_config),
            patch("builtins.input", return_value="n"),
        ):
            from ncatbot.cli.commands.plugin_commands import create_plugin_template

            create_plugin_template("existing", non_interactive=False)

            # 目录应该仍然存在但没有被填充模板
            assert (temp_plugins_dir / "existing").exists()

    def test_create_plugin_overwrite_confirm(self, mock_config, temp_plugins_dir):
        """测试确认覆盖"""
        # 先创建一个插件目录
        existing_dir = temp_plugins_dir / "existing"
        existing_dir.mkdir()
        (existing_dir / "old_file.txt").write_text("old content")

        with (
            patch("ncatbot.cli.commands.plugin_commands.config", mock_config),
            patch("builtins.input", return_value="y"),
        ):
            from ncatbot.cli.commands.plugin_commands import create_plugin_template

            create_plugin_template("existing", non_interactive=False)

            # 旧文件应该被删除
            assert not (existing_dir / "old_file.txt").exists()
            # 新模板文件应该存在
            assert (existing_dir / "manifest.toml").exists()


class TestRemovePlugin:
    """remove_plugin 命令测试"""

    def test_remove_plugin(self, mock_config, sample_plugin, capsys):
        """测试删除插件"""
        with (
            patch("ncatbot.cli.commands.plugin_commands.config", mock_config),
            patch("builtins.input", return_value="y"),
        ):
            from ncatbot.cli.commands.plugin_commands import remove_plugin

            remove_plugin("sample_plugin")

            assert not sample_plugin.exists()
            captured = capsys.readouterr()
            assert "已删除" in captured.out

    def test_remove_plugin_not_exist(self, mock_config, temp_plugins_dir, capsys):
        """测试删除不存在的插件"""
        with patch("ncatbot.cli.commands.plugin_commands.config", mock_config):
            from ncatbot.cli.commands.plugin_commands import remove_plugin

            remove_plugin("nonexistent")

            captured = capsys.readouterr()
            assert "不存在" in captured.out

    def test_remove_plugin_cancel(self, mock_config, sample_plugin, capsys):
        """测试取消删除"""
        with (
            patch("ncatbot.cli.commands.plugin_commands.config", mock_config),
            patch("builtins.input", return_value="n"),
        ):
            from ncatbot.cli.commands.plugin_commands import remove_plugin

            remove_plugin("sample_plugin")

            assert sample_plugin.exists()
            captured = capsys.readouterr()
            assert "已取消" in captured.out


class TestListPlugins:
    """list_plugins 命令测试"""

    def test_list_plugins_empty(self, mock_config, temp_plugins_dir, capsys):
        """测试列出空目录"""
        with patch("ncatbot.cli.commands.plugin_commands.config", mock_config):
            from ncatbot.cli.commands.plugin_commands import list_plugins

            list_plugins()

            captured = capsys.readouterr()
            assert "没有安装" in captured.out

    def test_list_plugins_with_plugin(self, mock_config, sample_plugin, capsys):
        """测试列出已安装插件"""
        with patch("ncatbot.cli.commands.plugin_commands.config", mock_config):
            from ncatbot.cli.commands.plugin_commands import list_plugins

            list_plugins()

            captured = capsys.readouterr()
            assert "sample_plugin" in captured.out
            assert "1.0.0" in captured.out
            assert "Test Author" in captured.out

    def test_list_plugins_without_manifest(self, mock_config, temp_plugins_dir, capsys):
        """测试没有 manifest 的插件"""
        # 创建一个没有 manifest 的插件目录
        (temp_plugins_dir / "broken_plugin").mkdir()

        with patch("ncatbot.cli.commands.plugin_commands.config", mock_config):
            from ncatbot.cli.commands.plugin_commands import list_plugins

            list_plugins()

            captured = capsys.readouterr()
            assert "broken_plugin" in captured.out
            assert "无 manifest" in captured.out

    def test_list_plugins_dir_not_exist(self, mock_config, capsys):
        """测试插件目录不存在"""
        mock_config.plugin.plugins_dir = "/nonexistent/path"

        with patch("ncatbot.cli.commands.plugin_commands.config", mock_config):
            from ncatbot.cli.commands.plugin_commands import list_plugins

            list_plugins()

            captured = capsys.readouterr()
            assert "不存在" in captured.out
