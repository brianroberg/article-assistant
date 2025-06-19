# Claude Code Development Guidelines

This document outlines the development practices and guidelines used when working with Claude Code on this project.

## Code Quality Standards

### Linting and Formatting
- **Always use Ruff** for both linting and formatting
- Run `ruff check .` before committing any code
- Run `ruff format .` to maintain consistent code style
- Fix all linting issues - never commit code with unresolved linting errors

### Testing Requirements
- **Comprehensive test coverage** is mandatory for all functions
- Write both unit tests and functional tests
- Unit tests should cover individual functions in isolation
- Functional tests should cover end-to-end behavior and integration
- All tests must pass before considering work complete
- Use pytest as the testing framework
- Use pytest-mock for mocking dependencies

### Test Commands
```bash
# Run all tests
python -m pytest

# Run with verbose output
python -m pytest -v

# Run specific test files
python -m pytest tests/test_extract_article_metadata.py
python -m pytest tests/test_functional.py

# Check code quality
ruff check .
ruff format .
```

## Project Structure

### Organization
- Keep main application code in the root directory
- Place all tests in a dedicated `tests/` subdirectory
- Include `__init__.py` in test directories to make them proper Python packages
- Use descriptive filenames that clearly indicate purpose

### Required Files
- `README.md` - Comprehensive project documentation
- `requirements.txt` - All Python dependencies with version constraints
- `.gitignore` - Comprehensive exclusion rules for Python projects
- `CLAUDE.md` - This development guidelines document

## Development Workflow

### Task Management
- Use the TodoWrite and TodoRead tools to track progress on complex tasks
- Break down large tasks into smaller, manageable subtasks
- Mark todos as `in_progress` when starting work (only one at a time)
- Mark todos as `completed` immediately upon finishing each task
- Update todo status in real-time as work progresses

### Code Development Process
1. **Plan**: Use TodoWrite to create a task breakdown for complex work
2. **Implement**: Write code following established patterns and conventions
3. **Test**: Create comprehensive unit and functional tests
4. **Lint**: Run Ruff to ensure code quality and consistency
5. **Verify**: Ensure all tests pass and code is properly formatted
6. **Document**: Update README and other documentation as needed

### Error Handling
- Implement comprehensive error handling for all external dependencies
- Use proper exit codes (0 for success, 1 for errors, 2 for argument errors)
- Provide informative error messages to users
- Handle network failures, parsing errors, and missing data gracefully

## Code Conventions

### Function Design
- Write single-purpose functions with clear responsibilities
- Use descriptive function and variable names
- Include comprehensive docstrings for all functions
- Follow the principle of separation of concerns

### Dependencies
- Minimize external dependencies
- Pin dependency versions in requirements.txt
- Use virtual environments for isolation
- Document the purpose of each dependency

### Command-Line Interface
- Use argparse for command-line argument handling
- Provide helpful help messages and usage examples
- Validate user inputs and provide clear error messages
- Support common CLI patterns (--help, --version, etc.)

## Testing Guidelines

### Unit Tests
- Test each function in isolation using mocks for external dependencies
- Cover both happy path and error conditions
- Test edge cases and boundary conditions
- Use descriptive test names that explain what is being tested

### Functional Tests
- Test complete workflows and integrations
- Use real data structures but mock external network calls
- Test command-line interface behavior
- Verify error handling and user experience

### Test Organization
```python
class TestFunctionName:
    """Test cases for the function_name function."""
    
    def test_basic_functionality(self):
        """Test basic happy path functionality."""
        pass
    
    def test_error_conditions(self):
        """Test error handling and edge cases."""
        pass
    
    def test_edge_cases(self):
        """Test boundary conditions and special cases."""
        pass
```

## Documentation Standards

### README Requirements
- Clear project description and purpose
- Installation instructions with virtual environment setup
- Usage examples with actual command syntax
- Development setup instructions
- Project structure overview
- Contributing guidelines

### Code Documentation
- Comprehensive docstrings for all public functions
- Inline comments for complex logic
- Type hints where beneficial for clarity
- Examples in docstrings for complex functions

## Git and Version Control

### Commit Practices
- User will manage git commits. Do not initiate git commits.
- Write clear, descriptive commit messages when requested by user

### Repository Structure
- Use .gitignore to exclude generated files, virtual environments, and IDE files
- Include all necessary files for project setup and development
- Keep the repository clean and focused on essential project files

## Python Best Practices

### Code Style
- Follow PEP 8 guidelines (enforced by Ruff)
- Use meaningful variable and function names
- Keep functions focused and reasonably sized
- Avoid global variables and side effects

### Error Handling
- Use specific exception types rather than generic Exception
- Provide helpful error messages with context
- Log errors appropriately for debugging
- Use try-except blocks judiciously, not as flow control

### Performance Considerations
- Use appropriate data structures for the task
- Avoid premature optimization
- Profile code when performance is critical
- Cache expensive operations when appropriate

## Continuous Improvement

### Code Review
- Review code for clarity, correctness, and maintainability
- Ensure all tests pass and code is properly formatted
- Verify documentation is complete and accurate
- Check for security issues and best practices

### Refactoring
- Regularly refactor to improve code clarity and structure
- Remove duplicate code and extract common functionality
- Update tests when refactoring to ensure continued coverage
- Maintain backward compatibility when possible

This document serves as a reference for maintaining high code quality and consistent development practices when working with Claude Code.