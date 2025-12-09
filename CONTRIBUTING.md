# Contributing to Ignition Zerobus Connector

Thank you for your interest in contributing to the Ignition Zerobus Connector project. This document provides guidelines and instructions for contributing.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Issue Guidelines](#issue-guidelines)
- [Community](#community)

---

## Code of Conduct

This project adheres to professional standards of conduct. By participating, you are expected to:

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Accept constructive criticism gracefully
- Focus on what is best for the community and project
- Show empathy towards other community members

---

## Getting Started

### Prerequisites

Before contributing, ensure you have:

- Java JDK 17 or later
- Gradle 8.0 or later
- Ignition Gateway 8.3.x or later (for testing)
- Git for version control
- An IDE (IntelliJ IDEA, Eclipse, or VS Code)

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/lakeflow-ignition-zerobus-connector.git
   cd lakeflow-ignition-zerobus-connector
   ```
3. Add upstream remote:
   ```bash
   git remote add upstream https://github.com/pravinva/lakeflow-ignition-zerobus-connector.git
   ```

---

## Development Setup

### Build the Module

```bash
cd module
./gradlew clean build
```

### Run Tests

```bash
./gradlew test
```

### Install Module Locally

```bash
./gradlew buildModule
# Module will be in: module/build/modules/zerobus-connector-1.0.0.modl
```

### Development Workflow

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes

3. Build and test:
   ```bash
   ./gradlew clean build test
   ```

4. Install and test in Ignition:
   ```bash
   # Copy to Ignition and restart
   sudo cp module/build/modules/*.modl /path/to/ignition/user-lib/modules/
   sudo systemctl restart ignition
   ```

5. Commit your changes:
   ```bash
   git add .
   git commit -m "Description of changes"
   ```

6. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

---

## How to Contribute

### Types of Contributions

We welcome contributions in the following areas:

#### Bug Fixes
- Fix reported issues
- Improve error handling
- Resolve edge cases

#### New Features
- Enhanced configuration options
- Additional tag selection modes
- Performance improvements
- Monitoring and diagnostics enhancements

#### Documentation
- Improve README and guides
- Add code comments
- Create tutorials and examples
- Fix typos and clarifications

#### Testing
- Add unit tests
- Create integration tests
- Improve test coverage
- Test on different Ignition versions

#### Code Quality
- Refactor existing code
- Improve performance
- Reduce technical debt
- Update dependencies

---

## Pull Request Process

### Before Submitting

1. **Sync with upstream**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Ensure all tests pass**:
   ```bash
   ./gradlew clean test
   ```

3. **Verify the build**:
   ```bash
   ./gradlew buildModule
   ```

4. **Test in Ignition**: Install and verify the module works

5. **Update documentation**: If your changes affect usage

### Submitting a Pull Request

1. **Title**: Use a clear, descriptive title
   - Good: "Fix NullPointerException in tag polling"
   - Bad: "Bug fix"

2. **Description**: Include:
   - Summary of changes
   - Related issue number (if applicable)
   - Testing performed
   - Screenshots (if UI changes)

3. **Commits**: 
   - Keep commits atomic and focused
   - Write clear commit messages
   - Follow conventional commit format (optional)

4. **Review**: Address reviewer feedback promptly

### Pull Request Template

```markdown
## Description
Brief description of changes

## Related Issue
Fixes #(issue number)

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Tested in Ignition Gateway
- [ ] Documentation updated

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No new warnings introduced
```

---

## Coding Standards

### Java Style Guide

Follow standard Java conventions:

#### Naming Conventions
- **Classes**: `PascalCase` (e.g., `TagSubscriptionService`)
- **Methods**: `camelCase` (e.g., `pollTagValues()`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_QUEUE_SIZE`)
- **Variables**: `camelCase` (e.g., `tagPath`, `eventCount`)

#### Code Organization
- **Package structure**: Follow existing structure
- **Class length**: Keep classes focused and under 500 lines
- **Method length**: Limit methods to 50 lines where possible
- **Comments**: Document complex logic and public APIs

#### Best Practices
- Use meaningful variable names
- Avoid magic numbers (use named constants)
- Handle exceptions appropriately
- Log important events and errors
- Use `@Override` annotation
- Avoid deep nesting (max 3 levels)

### Example

```java
public class TagSubscriptionService {
    private static final int DEFAULT_BATCH_SIZE = 10;
    private static final Logger logger = LoggerFactory.getLogger(TagSubscriptionService.class);
    
    private final GatewayContext gatewayContext;
    private final ConfigModel config;
    
    /**
     * Polls tag values at configured interval.
     * 
     * @throws TimeoutException if tag read times out
     */
    private void pollTagValues() throws TimeoutException {
        // Implementation
    }
}
```

### Gradle Build Files

- Keep dependencies up to date
- Document non-obvious dependencies
- Use version variables for consistency

---

## Testing Guidelines

### Unit Tests

Write unit tests for:
- Business logic
- Data transformations
- Error handling
- Edge cases

Example:
```java
@Test
public void testTagEventCreation() {
    TagEvent event = new TagEvent(
        "[Sample_Tags]Sine0",
        42.0,
        "Good",
        new Date()
    );
    
    assertEquals("[Sample_Tags]Sine0", event.getTagPath());
    assertEquals(42.0, event.getValue());
    assertEquals("Good", event.getQuality());
}
```

### Integration Tests

Test integration with:
- Ignition Tag Manager
- Zerobus SDK
- Configuration persistence

### Manual Testing

Before submitting, test:
1. Module installation
2. Configuration via REST API
3. Tag subscription
4. Data streaming to Databricks
5. Error scenarios
6. Module restart/shutdown

---

## Documentation

### Code Documentation

- **Public APIs**: Must have Javadoc
- **Complex logic**: Add inline comments
- **Configuration**: Document all options
- **Examples**: Provide usage examples

### User Documentation

When adding features, update:
- `README.md` - Main documentation
- `docs/HANDOVER.md` - User guide
- `examples/` - Configuration examples
- `docs/developer.md` - Developer guide

### Documentation Style

- Use clear, concise language
- Provide examples
- Include screenshots (for UI features)
- Keep documentation up to date

---

## Issue Guidelines

### Reporting Bugs

Use the bug report template and include:

```markdown
**Describe the bug**
Clear description of the issue

**To Reproduce**
Steps to reproduce:
1. Install module version X
2. Configure with settings Y
3. Observe error Z

**Expected behavior**
What should happen

**Environment**
- Ignition version: 8.3.2
- Module version: 1.0.0
- OS: Ubuntu 20.04
- Java version: 17

**Logs**
```
Relevant log entries
```

**Additional context**
Any other relevant information
```

### Requesting Features

Use the feature request template:

```markdown
**Feature Description**
Clear description of the proposed feature

**Use Case**
Describe the problem this solves

**Proposed Solution**
How should this feature work?

**Alternatives Considered**
Other approaches you've considered

**Additional Context**
Related issues, references, etc.
```

### Asking Questions

- Check existing documentation first
- Search closed issues
- Use GitHub Discussions for questions
- Provide context and examples

---

## Community

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and general discussion
- **Pull Requests**: Code review and feedback

### Getting Help

- Review the documentation in `docs/`
- Check existing issues and discussions
- Ask specific, well-formed questions
- Provide relevant context and logs

### Response Times

- We aim to respond to issues within 3-5 business days
- Pull requests may take 1-2 weeks for review
- Complex features may require discussion before implementation

---

## Roadmap

### Planned Features

#### High Priority
- **Configuration GUI**: Web-based configuration interface in Ignition Gateway
- **Tag Browsing**: Browse available tags in configuration
- **Metrics Dashboard**: Real-time metrics visualization
- **Batch Operations**: Bulk tag operations

#### Medium Priority
- **TLS Configuration**: Custom SSL/TLS settings
- **Data Transformation**: Pre-send data transformations
- **Alert System**: Configurable alerts for failures
- **Multi-Workspace**: Support multiple Databricks workspaces

#### Low Priority
- **Historical Backfill**: Backfill historical data
- **Tag Groups**: Logical tag grouping
- **Custom Protocols**: Additional ingestion protocols
- **Mobile Dashboard**: Mobile monitoring app

### Contributing to Roadmap

To propose new features:
1. Open a feature request issue
2. Describe the use case and benefits
3. Discuss implementation approach
4. Wait for maintainer feedback before starting work

---

## Development Best Practices

### Version Control

- **Branch naming**: `feature/`, `bugfix/`, `docs/`, `refactor/`
- **Commit messages**: Clear and descriptive
- **Squash commits**: Before merging (if needed)
- **Rebase**: Keep history clean

### Code Review

When reviewing:
- Be constructive and respectful
- Focus on code quality and correctness
- Suggest improvements
- Approve or request changes clearly

When receiving reviews:
- Address all feedback
- Ask questions if unclear
- Make requested changes
- Thank reviewers

### Security

- Never commit secrets or credentials
- Use environment variables for sensitive data
- Report security issues privately
- Follow secure coding practices

---

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0, the same license as the project.

---

## Questions?

If you have questions about contributing, please:
1. Check the documentation
2. Search existing issues
3. Open a new discussion
4. Contact the maintainers

Thank you for contributing to the Ignition Zerobus Connector!

