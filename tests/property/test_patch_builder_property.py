"""Property-based tests for patch builder using Hypothesis."""

import pytest
from hypothesis import given, strategies as st
from src.core.patch_builder import PatchBuilder


class TestPatchBuilderProperty:
    """Property-based tests for PatchBuilder."""

    def setup_method(self):
        """Set up patch builder."""
        self.builder = PatchBuilder()

    def test_builder_initialized(self):
        """Test that builder can be initialized."""
        assert self.builder is not None

    @given(
        st.dictionaries(st.text(min_size=1, max_size=20), st.text(min_size=1, max_size=50)),
        st.text(min_size=1, max_size=100)
    )
    def test_build_patch_always_returns_patch_result(self, original_files: dict, 
                                                    llm_response: str):
        """Property: build_patch always returns a PatchResult."""
        result = self.builder.build_patch(original_files, llm_response)
        assert hasattr(result, 'success')
        assert hasattr(result, 'patch_content')
        assert hasattr(result, 'files_modified')
        assert hasattr(result, 'files_created')
        assert isinstance(result.success, bool)

    @given(
        st.dictionaries(st.text(min_size=1, max_size=20), st.text(min_size=1, max_size=50)),
        st.text(min_size=1, max_size=100)
    )
    def test_build_patch_handles_empty_response(self, original_files: dict, 
                                               llm_response: str):
        """Property: patch handles empty LLM response."""
        result = self.builder.build_patch(original_files, "")
        assert hasattr(result, 'success')
        assert isinstance(result.success, bool)

    @given(
        st.dictionaries(st.text(min_size=1, max_size=20), st.text(min_size=1, max_size=50)),
        st.text(min_size=1, max_size=100)
    )
    def test_build_patch_has_files_lists(self, original_files: dict, 
                                        llm_response: str):
        """Property: patch result has files lists."""
        result = self.builder.build_patch(original_files, llm_response)
        assert hasattr(result, 'files_modified')
        assert hasattr(result, 'files_created')
        assert isinstance(result.files_modified, list)
        assert isinstance(result.files_created, list)

    @given(
        st.dictionaries(st.text(min_size=1, max_size=20), st.text(min_size=1, max_size=50)),
        st.text(min_size=1, max_size=100)
    )
    def test_build_patch_has_error_handling(self, original_files: dict, 
                                           llm_response: str):
        """Property: patch has error handling."""
        result = self.builder.build_patch(original_files, llm_response)
        assert hasattr(result, 'error_message')
        # error_message can be None or string
        assert result.error_message is None or isinstance(result.error_message, str)

    @given(
        st.dictionaries(st.text(min_size=1, max_size=20), st.text(min_size=1, max_size=50)),
        st.text(min_size=1, max_size=100)
    )
    def test_build_patch_handles_special_chars(self, original_files: dict, 
                                              llm_response: str):
        """Property: patch handles special characters gracefully."""
        special_chars = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        response_with_special = llm_response + special_chars
        
        result = self.builder.build_patch(original_files, response_with_special)
        
        # Should still be a valid PatchResult
        assert hasattr(result, 'success')
        assert isinstance(result.success, bool)
        
        # Should not crash
        assert hasattr(result, 'patch_content')
        assert hasattr(result, 'files_modified')
        assert hasattr(result, 'files_created') 