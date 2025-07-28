"""Tests for patch builder functionality."""
import os
import tempfile
from unittest.mock import mock_open, patch

from src.core.patch_builder import patch_builder


class TestPatchBuilder:
    """Test cases for PatchBuilder."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test_file.py")

        # Create a test file
        with open(self.test_file, "w") as f:
            f.write("def original_function():\n    return 'original'\n")

    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_extract_code_blocks_single_file(self):
        """Test extracting code blocks from LLM response."""
        llm_response = """
Here's the updated function:

```python
def updated_function():
    return 'updated'
```
"""
        blocks = patch_builder._extract_code_blocks(llm_response)

        assert len(blocks) == 1
        assert blocks[0].language == "python"
        assert blocks[0].file_path == "updated_function.py"  # Should infer from function name
        assert blocks[0].content == "def updated_function():\n    return 'updated'"
        assert not blocks[0].is_new_file

    def test_extract_code_blocks_with_file_path(self):
        """Test extracting code blocks with explicit file paths."""
        llm_response = """
Here are the changes:

```python src/main.py
from fastapi import FastAPI

app = FastAPI()
```

```python tests/test_main.py
def test_app():
    assert True
```
"""
        blocks = patch_builder._extract_code_blocks(llm_response)

        assert len(blocks) == 2
        assert blocks[0].language == "python"
        assert blocks[0].file_path == "src/main.py"
        assert blocks[0].content == "from fastapi import FastAPI\n\napp = FastAPI()"
        assert not blocks[0].is_new_file

        assert blocks[1].language == "python"
        assert blocks[1].file_path == "tests/test_main.py"
        assert blocks[1].content == "def test_app():\n    assert True"
        assert not blocks[1].is_new_file

    def test_extract_code_blocks_new_file_indicator(self):
        """Test detecting new file indicators."""
        llm_response = """
Create a new configuration file:

```python config/settings.py
# New file
DEBUG = True
DATABASE_URL = "sqlite:///app.db"
```
"""
        blocks = patch_builder._extract_code_blocks(llm_response)

        assert len(blocks) == 1
        assert blocks[0].language == "python"
        assert blocks[0].file_path == "config/settings.py"
        assert blocks[0].content == "# New file\nDEBUG = True\nDATABASE_URL = \"sqlite:///app.db\""
        assert blocks[0].is_new_file

    def test_extract_code_blocks_mixed_content(self):
        """Test extracting blocks from mixed content."""
        llm_response = """
Let me explain the changes:

First, we need to update the main function:

```python src/main.py
def main():
    print("Hello, World!")
```

Then create a new test file:

```python tests/test_main.py
def test_main():
    assert True
```

And update the README:

```markdown README.md
# Updated Project
This is the updated README.
```
"""
        blocks = patch_builder._extract_code_blocks(llm_response)

        assert len(blocks) == 3
        assert blocks[0].file_path == "src/main.py"
        assert blocks[1].file_path == "tests/test_main.py"
        assert blocks[2].file_path == "README.md"

    def test_infer_file_path_from_content(self):
        """Test inferring file path from code content."""
        # Test Python file inference
        content = "from fastapi import FastAPI\n\napp = FastAPI()"
        path = patch_builder._infer_file_path(content, "python")
        assert path == "main.py"  # Default inference

        # Test test file inference
        content = "import pytest\n\ndef test_something():\n    assert True"
        path = patch_builder._infer_file_path(content, "python")
        assert path == "test_main.py"  # Should infer test file

        # Test config file inference
        content = "DEBUG = True\nDATABASE_URL = 'sqlite:///app.db'"
        path = patch_builder._infer_file_path(content, "python")
        assert path == "config.py"  # Should infer config file

    def test_build_modification_patch(self):
        """Test building patch for file modification."""
        original_content = "def original_function():\n    return 'original'\n"
        new_content = "def updated_function():\n    return 'updated'\n"

        patch_content = patch_builder._build_modification_patch(
            "test_file.py", original_content, new_content
        )

        assert "--- a/test_file.py" in patch_content
        assert "+++ b/test_file.py" in patch_content
        assert "-def original_function():" in patch_content
        assert "+def updated_function():" in patch_content

    def test_build_creation_patch(self):
        """Test building patch for new file creation."""
        content = "def new_function():\n    return 'new'\n"

        patch_content = patch_builder._build_creation_patch("new_file.py", content)

        assert "--- /dev/null" in patch_content
        assert "+++ b/new_file.py" in patch_content
        assert "+def new_function():" in patch_content

    def test_build_patch_single_file_modification(self):
        """Test building patch for single file modification."""
        original_files = {"test_file.py": "def original_function():\n    return 'original'\n"}

        llm_response = """
Update the function:

```python
def updated_function():
    return 'updated'
```
"""

        with patch('builtins.open', mock_open(read_data="def original_function():\n    return 'original'\n")):
            result = patch_builder.build_patch(original_files, llm_response)

        assert result.success
        assert "test_file.py" in result.files_modified
        assert len(result.files_created) == 0
        assert "--- a/test_file.py" in result.patch_content
        assert "+++ b/test_file.py" in result.patch_content

    def test_build_patch_multiple_files(self):
        """Test building patch for multiple files."""
        original_files = {
            "src/main.py": "def main():\n    pass\n",
            "tests/test_main.py": "def test_main():\n    pass\n"
        }

        llm_response = """
Update multiple files:

```python src/main.py
def main():
    print("Hello, World!")
```

```python tests/test_main.py
def test_main():
    assert True
```
"""

        with patch('builtins.open', mock_open(read_data="def main():\n    pass\n")):
            result = patch_builder.build_patch(original_files, llm_response)

        assert result.success
        assert len(result.files_modified) == 2
        assert "src/main.py" in result.files_modified
        assert "tests/test_main.py" in result.files_modified
        assert len(result.files_created) == 0

    def test_build_patch_new_file_creation(self):
        """Test building patch for new file creation."""
        original_files = {}

        llm_response = """
Create a new configuration file:

```python config/settings.py
DEBUG = True
DATABASE_URL = "sqlite:///app.db"
```
"""

        result = patch_builder.build_patch(original_files, llm_response)

        assert result.success
        assert len(result.files_modified) == 0
        assert len(result.files_created) == 1
        assert "config/settings.py" in result.files_created
        assert "--- /dev/null" in result.patch_content
        assert "+++ b/config/settings.py" in result.patch_content

    def test_build_patch_mixed_modifications(self):
        """Test building patch with both modifications and new files."""
        original_files = {"src/main.py": "def main():\n    pass\n"}

        llm_response = """
Update existing file and create new one:

```python src/main.py
def main():
    print("Updated main")
```

```python tests/test_main.py
def test_main():
    assert True
```
"""

        with patch('builtins.open', mock_open(read_data="def main():\n    pass\n")):
            result = patch_builder.build_patch(original_files, llm_response)

        assert result.success
        assert len(result.files_modified) == 1
        assert "src/main.py" in result.files_modified
        assert len(result.files_created) == 1
        assert "tests/test_main.py" in result.files_created

    def test_build_patch_no_code_blocks(self):
        """Test building patch with no code blocks."""
        original_files = {"test_file.py": "def main():\n    pass\n"}

        llm_response = "This is just text with no code blocks."

        result = patch_builder.build_patch(original_files, llm_response)

        assert not result.success
        assert "No code blocks found" in result.error_message

    def test_build_patch_ambiguous_file_path(self):
        """Test building patch with ambiguous file paths."""
        original_files = {"main.py": "def main():\n    pass\n"}

        llm_response = """
Update the function:

```python
def updated_function():
    return 'updated'
```
"""

        with patch('builtins.open', mock_open(read_data="def main():\n    pass\n")):
            result = patch_builder.build_patch(original_files, llm_response)

        # Should infer the file path and succeed
        assert result.success
        assert len(result.files_modified) == 1

    def test_validate_patch_valid(self):
        """Test validating a valid patch."""
        patch_content = """--- a/test_file.py
+++ b/test_file.py
@@ -1,2 +1,2 @@
-def original_function():
-    return 'original'
+def updated_function():
+    return 'updated'
"""

        result = patch_builder.validate_patch(patch_content)
        assert result.success
        assert result.error_message is None

    def test_validate_patch_invalid_format(self):
        """Test validating an invalid patch format."""
        patch_content = "This is not a valid patch format"

        result = patch_builder.validate_patch(patch_content)
        assert not result.success
        assert "Invalid patch format" in result.error_message

    def test_validate_patch_empty(self):
        """Test validating an empty patch."""
        result = patch_builder.validate_patch("")
        assert not result.success
        assert "Empty patch" in result.error_message

    def test_validate_patch_missing_file_headers(self):
        """Test validating patch missing file headers."""
        patch_content = """@@ -1,2 +1,2 @@
-def original_function():
-    return 'original'
+def updated_function():
+    return 'updated'
"""

        result = patch_builder.validate_patch(patch_content)
        assert not result.success
        assert "Missing file headers" in result.error_message
