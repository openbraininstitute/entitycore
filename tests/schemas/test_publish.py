from app.schemas.publish import MoveAssetsResult, MoveDirectoryResult, MoveFileResult


def test_move_directory_result_update_from_file_result_with_error():
    result = MoveDirectoryResult()
    result.update_from_file_result(MoveFileResult(size=10, error="some error"))

    assert result.size == 10
    assert result.file_count == 1
    assert result.errors == ["some error"]


def test_move_directory_result_update_from_file_result_without_error():
    result = MoveDirectoryResult()
    result.update_from_file_result(MoveFileResult(size=10, error=None))

    assert result.size == 10
    assert result.file_count == 1
    assert result.errors == []


def test_move_assets_result_update_from_file_result_with_error():
    result = MoveAssetsResult()
    result.update_from_file_result(MoveFileResult(size=5, error="file error"))

    assert result.total_size == 5
    assert result.file_count == 1
    assert result.asset_count == 1
    assert result.errors == ["file error"]


def test_move_assets_result_update_from_file_result_without_error():
    result = MoveAssetsResult()
    result.update_from_file_result(MoveFileResult(size=5, error=None))

    assert result.total_size == 5
    assert result.file_count == 1
    assert result.asset_count == 1
    assert result.errors == []


def test_move_assets_result_update_from_directory_result_with_errors():
    result = MoveAssetsResult()
    dir_result = MoveDirectoryResult(size=20, file_count=3, errors=["err1", "err2"])
    result.update_from_directory_result(dir_result)

    assert result.total_size == 20
    assert result.file_count == 3
    assert result.asset_count == 1
    assert result.errors == ["err1", "err2"]


def test_move_assets_result_update_from_directory_result_without_errors():
    result = MoveAssetsResult()
    dir_result = MoveDirectoryResult(size=20, file_count=3)
    result.update_from_directory_result(dir_result)

    assert result.total_size == 20
    assert result.file_count == 3
    assert result.asset_count == 1
    assert result.errors == []
