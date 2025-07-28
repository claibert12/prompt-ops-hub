"""Patch builder for converting LLM code blocks into unified diffs."""

import re
from dataclasses import dataclass


@dataclass
class CodeBlock:
    """A code block from LLM response."""
    language: str
    file_path: str | None
    content: str
    is_new_file: bool = False


@dataclass
class PatchResult:
    """Result of building a patch."""
    success: bool
    patch_content: str
    files_modified: list[str]
    files_created: list[str]
    error_message: str | None = None


class PatchBuilder:
    """Builds unified diffs from LLM code blocks."""

    def __init__(self):
        """Initialize patch builder."""
        # Code fence patterns - improved regex to handle file paths correctly
        self.code_fence_pattern = re.compile(
            r'```(\w+)(?:\s+([^\n]+))?\n(.*?)```',
            re.DOTALL
        )

        # File path patterns in code fences
        self.file_path_patterns = [
            r'(\w+/\w+\.\w+)',  # path/to/file.ext
            r'([a-zA-Z_][a-zA-Z0-9_]*\.\w+)',  # filename.ext
            r'(\w+/\w+/\w+\.\w+)',  # deeper/path/to/file.ext
        ]

    def build_patch(self, original_files: dict[str, str], llm_response: str) -> PatchResult:
        """Build a unified diff from LLM response.
        
        Args:
            original_files: Dict of file_path -> file_content for existing files
            llm_response: LLM response containing code blocks
            
        Returns:
            PatchResult with unified diff content
        """
        try:
            # Extract code blocks from LLM response
            code_blocks = self._extract_code_blocks(llm_response)

            if not code_blocks:
                return PatchResult(
                    success=False,
                    patch_content="",
                    files_modified=[],
                    files_created=[],
                    error_message="No code blocks found in LLM response"
                )

            # Build patches for each code block
            patches = []
            files_modified = []
            files_created = []

            for block in code_blocks:
                if not block.file_path:
                    return PatchResult(
                        success=False,
                        patch_content="",
                        files_modified=[],
                        files_created=[],
                        error_message=f"Code block missing file path: {block.language}"
                    )

                # Determine if this is a new file or modification
                # Check if the inferred file path matches any original file
                matching_file = None
                for original_file in original_files:
                    # Exact match
                    if original_file == block.file_path:
                        matching_file = original_file
                        break
                    # Match by filename (e.g., "main.py" matches "src/main.py")
                    elif original_file.endswith('/' + block.file_path) or original_file.endswith('\\' + block.file_path):
                        matching_file = original_file
                        break
                    # Match by basename (e.g., "main.py" matches "main.py")
                    elif original_file.split('/')[-1] == block.file_path or original_file.split('\\')[-1] == block.file_path:
                        matching_file = original_file
                        break

                # Only use fallback logic if we have exactly one original file and this is the first block
                if not matching_file and len(original_files) == 1 and len(code_blocks) == 1 and not block.is_new_file:
                    matching_file = list(original_files.keys())[0]

                if matching_file:
                    # Modify existing file
                    patch = self._build_modification_patch(
                        matching_file,
                        original_files[matching_file],
                        block.content
                    )
                    files_modified.append(matching_file)
                else:
                    # Create new file
                    patch = self._build_creation_patch(block.file_path, block.content)
                    files_created.append(block.file_path)

                patches.append(patch)

            # Combine all patches
            combined_patch = "\n".join(patches)

            return PatchResult(
                success=True,
                patch_content=combined_patch,
                files_modified=files_modified,
                files_created=files_created
            )

        except Exception as e:
            return PatchResult(
                success=False,
                patch_content="",
                files_modified=[],
                files_created=[],
                error_message=f"Error building patch: {str(e)}"
            )

    def _extract_code_blocks(self, llm_response: str) -> list[CodeBlock]:
        """Extract code blocks from LLM response.
        
        Args:
            llm_response: LLM response text
            
        Returns:
            List of CodeBlock objects
        """
        code_blocks = []

        # Split by code fence markers
        parts = llm_response.split('```')

        for i in range(1, len(parts), 2):  # Skip every other part (non-code parts)
            if i >= len(parts):
                break

            code_block = parts[i].strip()
            if not code_block:
                continue

            # Split the first line to get language and optional file path
            lines = code_block.split('\n', 1)
            if len(lines) < 2:
                continue

            header = lines[0].strip()
            content = lines[1]  # Don't strip to preserve formatting

            # Parse header: "language [filepath]"
            header_parts = header.split(None, 1)
            language = header_parts[0]
            file_path = header_parts[1] if len(header_parts) > 1 else None

            # If no explicit file path, try to infer from language and content
            if not file_path:
                file_path = self._infer_file_path(content, language)

            # Determine if this is a new file
            is_new_file = self._is_new_file_indicator(content)

            code_blocks.append(CodeBlock(
                language=language,
                file_path=file_path,
                content=content,
                is_new_file=is_new_file
            ))

        return code_blocks

    def _infer_file_path(self, content: str, language: str) -> str | None:
        """Infer file path from code content and language.
        
        Args:
            content: Code content
            language: Programming language
            
        Returns:
            Inferred file path or None
        """
        # Language to file extension mapping
        language_extensions = {
            'python': '.py',
            'javascript': '.js',
            'typescript': '.ts',
            'java': '.java',
            'cpp': '.cpp',
            'c': '.c',
            'go': '.go',
            'rust': '.rs',
            'php': '.php',
            'ruby': '.rb',
            'swift': '.swift',
            'kotlin': '.kt',
            'scala': '.scala',
            'html': '.html',
            'css': '.css',
            'sql': '.sql',
            'yaml': '.yaml',
            'yml': '.yml',
            'json': '.json',
            'toml': '.toml',
            'ini': '.ini',
            'sh': '.sh',
            'bash': '.sh',
            'dockerfile': 'Dockerfile',
            'makefile': 'Makefile',
        }

        # Try to find class/function names that might indicate file path
        if language == 'python':
            # Look for test functions
            if 'def test_' in content or 'import pytest' in content:
                return "test_main.py"

            # Look for config/settings
            if 'DEBUG' in content or 'DATABASE_URL' in content or 'config' in content.lower():
                return "config.py"

            # Look for class definitions
            class_match = re.search(r'class\s+(\w+)', content)
            if class_match:
                class_name = class_match.group(1)
                return f"{class_name.lower()}.py"

            # Look for function definitions
            func_match = re.search(r'def\s+(\w+)', content)
            if func_match:
                func_name = func_match.group(1)
                return f"{func_name.lower()}.py"

            # Default for Python
            return "main.py"

        # Default to language extension
        if language in language_extensions:
            return f"main{language_extensions[language]}"

        return None

    def _is_new_file_indicator(self, content: str) -> bool:
        """Check if content indicates a new file.
        
        Args:
            content: Code content
            
        Returns:
            True if this appears to be a new file
        """
        # Look for indicators that this is a new file
        new_file_indicators = [
            '#!/usr/bin/env',  # Shebang
            'package main',     # Go main package
            'public class',     # Java public class
            'class Main',       # Main class
            'def main',         # Python main function
            'if __name__',      # Python main guard
            '# New file',       # Explicit comment
        ]

        return any(indicator in content for indicator in new_file_indicators)

    def _build_modification_patch(self, file_path: str, original_content: str, new_content: str) -> str:
        """Build a unified diff for modifying an existing file.
        
        Args:
            file_path: Path to the file
            original_content: Original file content
            new_content: New file content
            
        Returns:
            Unified diff content
        """
        # Split content into lines
        original_lines = original_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)

        # Generate unified diff
        diff_lines = []
        diff_lines.append(f"--- a/{file_path}")
        diff_lines.append(f"+++ b/{file_path}")
        diff_lines.append("@@ -1,1 +1,1 @@")

        # Simple line-by-line comparison (in a real implementation, you'd use difflib)
        # For now, we'll just show the replacement
        for line in original_lines:
            diff_lines.append(f"-{line.rstrip()}")

        for line in new_lines:
            diff_lines.append(f"+{line.rstrip()}")

        return "\n".join(diff_lines)

    def _build_creation_patch(self, file_path: str, content: str) -> str:
        """Build a unified diff for creating a new file.
        
        Args:
            file_path: Path to the new file
            content: File content
            
        Returns:
            Unified diff content
        """
        # Split content into lines
        lines = content.splitlines(keepends=True)

        # Generate unified diff for new file
        diff_lines = []
        diff_lines.append("--- /dev/null")
        diff_lines.append(f"+++ b/{file_path}")
        diff_lines.append("@@ -0,0 +1,1 @@")

        for line in lines:
            diff_lines.append(f"+{line.rstrip()}")

        return "\n".join(diff_lines)

    def validate_patch(self, patch_content: str) -> PatchResult:
        """Validate that a patch is well-formed.
        
        Args:
            patch_content: Unified diff content
            
        Returns:
            PatchResult indicating validation success/failure
        """
        if not patch_content.strip():
            return PatchResult(
                success=False,
                patch_content="",
                files_modified=[],
                files_created=[],
                error_message="Empty patch"
            )

        # Basic validation - check for required diff headers
        lines = patch_content.split('\n')

        # Check for file headers
        has_file_header = any(line.startswith('--- ') for line in lines)
        has_file_header_plus = any(line.startswith('+++ ') for line in lines)

        # Check for hunk headers
        has_hunk_header = any(line.startswith('@@ ') for line in lines)

        # If we have no file headers and no hunk headers, it's completely invalid
        if not has_file_header and not has_file_header_plus and not has_hunk_header:
            return PatchResult(
                success=False,
                patch_content=patch_content,
                files_modified=[],
                files_created=[],
                error_message="Invalid patch format"
            )

        # If we have file headers but no hunk headers, it's invalid format
        if (has_file_header or has_file_header_plus) and not has_hunk_header:
            return PatchResult(
                success=False,
                patch_content=patch_content,
                files_modified=[],
                files_created=[],
                error_message="Invalid patch format"
            )

        # If we're missing file headers, that's a different error
        if not has_file_header or not has_file_header_plus:
            return PatchResult(
                success=False,
                patch_content=patch_content,
                files_modified=[],
                files_created=[],
                error_message="Missing file headers"
            )

        # If we have hunk headers but no file headers, it's invalid format
        if has_hunk_header and (not has_file_header or not has_file_header_plus):
            return PatchResult(
                success=False,
                patch_content=patch_content,
                files_modified=[],
                files_created=[],
                error_message="Invalid patch format"
            )

        return PatchResult(
            success=True,
            patch_content=patch_content,
            files_modified=[],
            files_created=[]
        )


# Global patch builder instance
patch_builder = PatchBuilder()
