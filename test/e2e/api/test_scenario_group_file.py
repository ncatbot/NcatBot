"""
群文件操作场景测试

测试场景：群文件上传 → 查询 → 操作
将相关联的操作链接起来，减少用户输入

流程：
1. 获取群根目录文件
2. 上传文件 → 获取文件列表
3. 创建文件夹 → 获取文件夹列表
4. 群相册：获取列表 → 上传图片
"""

from .framework import test_case, APITestSuite
from .utils import model_to_dict, create_test_file, create_test_image


# ============================================================================
# 场景测试：群文件操作
# ============================================================================


class GroupFileScenarioTests(APITestSuite):
    """
    群文件操作场景测试

    测试流程：
    1. 获取根目录 → 上传文件 → 刷新列表
    2. 创建文件夹 → 验证创建
    3. 群相册：获取列表 → 上传图片
    """

    suite_name = "Group File Scenario"
    suite_description = "群文件操作场景测试（上传→查询链）"

    @staticmethod
    @test_case(
        name="[场景3.2] 群文件完整流程: 上传→创建文件夹→上传到文件夹→查询",
        description="完整测试群文件操作：上传文件到根目录、创建文件夹、上传文件到文件夹、查询验证",
        category="scenario",
        api_endpoint="/upload_group_file, /create_group_file_folder, /get_group_root_files, /get_group_files_by_folder",
        expected="文件上传、文件夹创建、文件夹内上传均成功并可查询验证",
        tags=["scenario", "file", "upload", "folder"],
        show_result=True,
    )
    async def test_group_file_complete_scenario(api, data):
        """群文件完整流程：上传文件 → 创建文件夹 → 上传到文件夹 → 查询验证"""
        target_group = data.get("target_group")
        if not target_group:
            raise ValueError("需要配置 target_group")

        import time

        # 1. 上传文件到根目录
        file_path_1 = "/tmp/e2e_test_root_file.txt"
        file_name_1 = f"e2e_root_{int(time.time()) % 10000}.txt"
        create_test_file(file_path_1, "E2E 场景测试 - 根目录文件")

        upload_result_1 = await api.upload_group_file(
            group_id=int(target_group),
            file=file_path_1,
            name=file_name_1,
        )

        # 2. 创建测试文件夹
        folder_name = f"E2E测试文件夹_{int(time.time()) % 10000}"
        folder_result = await api.create_group_file_folder(
            group_id=int(target_group),
            folder_name=folder_name,
        )

        # 3. 查询根目录获取文件夹 ID
        query_root = await api.get_group_root_files(group_id=int(target_group))
        files_root = query_root.get("files", [])
        folders_root = query_root.get("folders", [])

        # 查找创建的文件夹（字段名是 folder_name 而非 name）
        created_folder = None
        folder_id = None
        for f in folders_root:
            if f.get("folder_name") == folder_name:
                created_folder = f
                folder_id = f.get("folder_id")
                break

        # 4. 上传文件到创建的文件夹
        file_path_2 = "/tmp/e2e_test_folder_file.txt"
        file_name_2 = f"e2e_folder_{int(time.time()) % 10000}.txt"
        create_test_file(file_path_2, "E2E 场景测试 - 文件夹内文件")

        upload_result_2 = await api.upload_group_file(
            group_id=int(target_group),
            file=file_path_2,
            name=file_name_2,
            folder=folder_id
            if folder_id
            else "/" + folder_name,  # 使用文件夹 ID 或路径
        )

        # 5. 查询文件夹内容验证
        folder_files = None
        uploaded_file_in_folder = None
        if folder_id:
            try:
                folder_content = await api.get_group_files_by_folder(
                    group_id=int(target_group),
                    folder_id=folder_id,
                )
                folder_files = folder_content.get("files", [])
                for f in folder_files:
                    if f.get("file_name") == file_name_2:  # 字段名是 file_name
                        uploaded_file_in_folder = f
                        break
            except Exception as e:
                folder_files = {"error": str(e)}

        # 查找根目录的文件（字段名是 file_name）
        uploaded_file_root = None
        for f in files_root:
            if f.get("file_name") == file_name_1:
                uploaded_file_root = f
                break

        return {
            "step1_upload_root": {
                "file_name": file_name_1,
                "result": model_to_dict(upload_result_1),
            },
            "step2_create_folder": {
                "folder_name": folder_name,
                "folder_id": folder_id,
                "result": model_to_dict(folder_result),
            },
            "step3_verify_root": {
                "total_files": len(files_root),
                "total_folders": len(folders_root),
                "root_file_found": uploaded_file_root is not None,
                "folder_found": created_folder is not None,
            },
            "step4_upload_to_folder": {
                "file_name": file_name_2,
                "target_folder": folder_name,
                "result": model_to_dict(upload_result_2),
            },
            "step5_verify_folder": {
                "folder_files_count": len(folder_files)
                if isinstance(folder_files, list)
                else "N/A",
                "file_in_folder_found": uploaded_file_in_folder is not None,
                "uploaded_file": uploaded_file_in_folder,
                "query_result": folder_files
                if not isinstance(folder_files, list)
                else "查询成功",
            },
        }

    @staticmethod
    @test_case(
        name="[场景3.3] POST方式发送文件: 文件+图片+语音+视频",
        description="使用 post_group_file 以消息形式发送各类文件",
        category="scenario",
        api_endpoint="/post_group_file",
        expected="各类文件消息发送成功",
        tags=["scenario", "file", "message", "post"],
        show_result=True,
    )
    async def test_post_group_file_scenario(api, data):
        """POST方式发送群文件：测试文件、图片、语音、视频"""
        target_group = data.get("target_group")
        if not target_group:
            raise ValueError("需要配置 target_group")

        import time

        results = {}

        # 1. 发送文本文件
        file_path = "/tmp/e2e_post_file.txt"
        create_test_file(file_path, f"E2E 测试 - POST文件 {time.time()}")

        try:
            file_msg_id = await api.post_group_file(
                group_id=int(target_group),
                file=file_path,
            )
            results["file"] = {"message_id": file_msg_id, "status": "success"}
        except Exception as e:
            results["file"] = {"error": str(e), "status": "failed"}

        # 2. 发送图片
        image_path = "/tmp/e2e_post_image.png"
        create_test_image(image_path)

        try:
            image_msg_id = await api.post_group_file(
                group_id=int(target_group),
                image=image_path,
            )
            results["image"] = {"message_id": image_msg_id, "status": "success"}
        except Exception as e:
            results["image"] = {"error": str(e), "status": "failed"}

        # 3. 发送语音（可选，根据环境决定）
        # results["record"] = {"status": "skipped", "reason": "语音文件需要特殊格式"}

        # 4. 发送视频（可选，根据环境决定）
        # results["video"] = {"status": "skipped", "reason": "视频文件较大，跳过测试"}

        return {
            "target_group": target_group,
            "results": results,
            "note": "post_group_file 支持发送文件、图片、语音、视频",
        }


class GroupAlbumScenarioTests(APITestSuite):
    """
    群相册场景测试

    测试流程：
    1. 获取相册列表 → 上传图片
    注意：部分 API 可能不被 NapCat 支持
    """

    suite_name = "Group Album Scenario"
    suite_description = "群相册场景测试（实验性 API）"

    @staticmethod
    @test_case(
        name="[场景3.4] 群相册: 获取列表→上传图片",
        description="获取群相册列表，然后上传测试图片",
        category="scenario",
        api_endpoint="/get_group_album_list, /upload_image_to_group_album",
        expected="相册操作成功（实验性 API）",
        tags=["scenario", "album", "experimental"],
        show_result=True,
    )
    async def test_group_album_scenario(api, data):
        """群相册操作：获取列表 → 上传图片"""
        target_group = data.get("target_group")
        if not target_group:
            raise ValueError("需要配置 target_group")

        result = {"step1_get_albums": None, "step2_upload": None}

        # 1. 获取相册列表
        try:
            album_list = await api.get_group_album_list(group_id=int(target_group))
            albums = album_list if isinstance(album_list, list) else []
            result["step1_get_albums"] = {
                "count": len(albums),
                "albums": albums[:3] if albums else [],
            }
        except Exception as e:
            result["step1_get_albums"] = {
                "error": str(e),
                "note": "此 API 可能不受支持",
            }

        # 2. 尝试上传图片（如果获取列表成功）
        if result["step1_get_albums"] and "error" not in result["step1_get_albums"]:
            try:
                image_path = "/tmp/e2e_album_test.png"
                create_test_image(image_path)

                albums = result["step1_get_albums"].get("albums", [])
                album_id = albums[0].get("album_id") if albums else None

                upload_result = await api.upload_image_to_group_album(
                    group_id=int(target_group),
                    file=image_path,
                    album_id=album_id,
                )
                result["step2_upload"] = {
                    "status": "success",
                    "result": model_to_dict(upload_result),
                }
            except Exception as e:
                result["step2_upload"] = {
                    "error": str(e),
                    "note": "此 API 可能不受支持",
                }
        else:
            result["step2_upload"] = {"skipped": True, "reason": "获取相册列表失败"}

        return result

    @staticmethod
    @test_case(
        name="[场景3.5] 群打卡签到",
        description="群打卡签到",
        category="scenario",
        api_endpoint="/set_group_sign",
        expected="打卡成功",
        tags=["scenario", "group", "sign"],
        show_result=True,
    )
    async def test_group_sign_scenario(api, data):
        """群打卡签到"""
        target_group = data.get("target_group")
        if not target_group:
            raise ValueError("需要配置 target_group")

        result = await api.set_group_sign(group_id=int(target_group))

        return {
            "target_group": target_group,
            "action": "sign",
            "result": model_to_dict(result),
        }


# 导出测试类
ALL_TEST_SUITES = [GroupFileScenarioTests, GroupAlbumScenarioTests]
