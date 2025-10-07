# Contributing to AI-Powered Personal Finance Assistant

🎉 First off, thanks for taking the time to contribute! Your involvement helps make this project better for everyone.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [Issue Guidelines](#issue-guidelines)
- [Testing Guidelines](#testing-guidelines)

## 🤝 Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md). Please read it before contributing.

## 🛠️ How Can I Contribute?

### 🐛 Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When creating a bug report, include:

- **Use a clear and descriptive title**
- **Describe the exact steps to reproduce the problem**
- **Provide specific examples** with sample code/data
- **Describe the behavior you observed** and what you expected
- **Include screenshots** if applicable
- **Specify your environment** (OS, Python version, Node.js version, etc.)

### 💡 Suggesting Enhancements

Enhancement suggestions are welcome! Please include:

- **Use a clear and descriptive title**
- **Provide a detailed description** of the suggested enhancement
- **Explain why this enhancement would be useful**
- **Include mockups or examples** if applicable

### 🔧 Code Contributions

1. Look for issues labeled `good first issue` or `help wanted`
2. Comment on the issue to express your interest
3. Fork the repository and create a feature branch
4. Make your changes following our coding standards
5. Write or update tests as needed
6. Ensure all tests pass
7. Submit a pull request

## 🏗️ Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL (or SQLite for development)
- Git

### Local Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/your-username/ai-finance-assistant.git
   cd ai-finance-assistant
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   cp .env.example .env.local
   # Edit .env.local with your configuration
   ```

4. **Database Setup**
   ```bash
   # For development with SQLite (easier)
   cd backend
   python -c "from app.database import init_db; init_db()"
   
   # For PostgreSQL (production-like)
   createdb financeai_dev
   alembic upgrade head
   ```

5. **Run the application**
   ```bash
   # Backend (in backend directory)
   uvicorn main:app --reload
   
   # Frontend (in frontend directory)
   npm start
   ```

## 📝 Coding Standards

### Python (Backend)

We use the following tools for code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking

```bash
# Format code
black .
isort .

# Check code quality
flake8 .
mypy .

# Or run all checks
make lint
```

### JavaScript/TypeScript (Frontend)

- **ESLint**: Linting
- **Prettier**: Code formatting

```bash
# Format code
npm run format

# Check code quality
npm run lint

# Fix linting issues
npm run lint:fix
```

### Code Style Guidelines

#### Python
- Follow PEP 8
- Use type hints for function parameters and return values
- Write docstrings for all public functions and classes
- Use meaningful variable and function names
- Keep functions small and focused

```python
from typing import List, Optional
from datetime import datetime

def categorize_transaction(
    description: str, 
    amount: float, 
    merchant: Optional[str] = None
) -> str:
    """
    Categorize a transaction based on description and merchant.
    
    Args:
        description: Transaction description
        amount: Transaction amount
        merchant: Optional merchant name
        
    Returns:
        Predicted category string
    """
    # Implementation here
    pass
```

#### JavaScript/React
- Use functional components with hooks
- Follow React best practices
- Use TypeScript for type safety
- Use meaningful component and variable names

```typescript
interface TransactionProps {
  transaction: Transaction;
  onUpdate: (transaction: Transaction) => void;
}

const TransactionCard: React.FC<TransactionProps> = ({ 
  transaction, 
  onUpdate 
}) => {
  // Component implementation
};
```

## 💬 Commit Messages

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

### Format
```
type(scope): description

[optional body]

[optional footer]
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples
```bash
feat(auth): add JWT token refresh functionality

fix(transactions): resolve duplicate transaction issue

docs(api): update API documentation for UPI endpoints

test(ai): add unit tests for transaction categorizer
```

## 🔄 Pull Request Process

1. **Create a feature branch** from `main`
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following coding standards

3. **Write or update tests** for your changes

4. **Run the test suite**
   ```bash
   # Backend tests
   cd backend && pytest
   
   # Frontend tests  
   cd frontend && npm test
   ```

5. **Update documentation** if needed

6. **Commit your changes** using conventional commit messages

7. **Push your branch** and create a pull request

8. **Fill out the PR template** completely

9. **Request review** from maintainers

### PR Requirements

- ✅ All tests must pass
- ✅ Code coverage should not decrease
- ✅ Follow coding standards
- ✅ Include proper documentation
- ✅ Link to related issues
- ✅ Add appropriate labels

### PR Template

```markdown
## Description
Brief description of what this PR does.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated and passing
```

## 🐛 Issue Guidelines

### Bug Reports

Use the bug report template and include:

- **Environment details** (OS, Python version, etc.)
- **Steps to reproduce**
- **Expected vs actual behavior**
- **Error messages or logs**
- **Screenshots** (if applicable)

### Feature Requests

Use the feature request template and include:

- **Problem description**
- **Proposed solution**
- **Alternative solutions considered**
- **Additional context**

### Labels

We use labels to categorize issues:

- `bug`: Something isn't working
- `enhancement`: New feature request
- `documentation`: Documentation improvements
- `good first issue`: Good for newcomers
- `help wanted`: Extra attention needed
- `priority/high`: High priority
- `ai/ml`: Related to AI/ML features
- `frontend`: Frontend-related
- `backend`: Backend-related

## 🧪 Testing Guidelines

### Backend Testing

We use **pytest** for backend testing:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_ai_modules.py

# Run tests with verbose output
pytest -v
```

### Test Structure
```python
import pytest
from app.ai_modules.transaction_categorizer import TransactionCategorizer

class TestTransactionCategorizer:
    
    @pytest.fixture
    def categorizer(self):
        return TransactionCategorizer()
    
    def test_categorize_food_transaction(self, categorizer):
        """Test categorization of food-related transaction."""
        result = categorizer.categorize(
            description="McDonald's purchase",
            amount=25.50
        )
        assert result == "Food & Dining"
    
    def test_invalid_input_handling(self, categorizer):
        """Test handling of invalid input."""
        with pytest.raises(ValueError):
            categorizer.categorize("", -10)
```

### Frontend Testing

We use **Jest** and **React Testing Library**:

```bash
# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Run specific test file
npm test TransactionCard.test.tsx
```

### Test Structure
```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import TransactionCard from '../TransactionCard';
import { mockTransaction } from '../../__mocks__/transactions';

describe('TransactionCard', () => {
  it('renders transaction information correctly', () => {
    render(<TransactionCard transaction={mockTransaction} />);
    
    expect(screen.getByText(mockTransaction.description)).toBeInTheDocument();
    expect(screen.getByText(`₹${mockTransaction.amount}`)).toBeInTheDocument();
  });
  
  it('calls onUpdate when edit button is clicked', () => {
    const mockOnUpdate = jest.fn();
    render(
      <TransactionCard 
        transaction={mockTransaction} 
        onUpdate={mockOnUpdate} 
      />
    );
    
    fireEvent.click(screen.getByText('Edit'));
    expect(mockOnUpdate).toHaveBeenCalledWith(mockTransaction);
  });
});
```

## 🚀 Release Process

1. **Version bumping** follows semantic versioning
2. **Changelog** is updated for each release
3. **Tags** are created for releases
4. **CI/CD** automatically deploys tagged releases

## 📚 Additional Resources

- [Project Wiki](https://github.com/your-username/ai-finance-assistant/wiki)
- [API Documentation](https://your-api.herokuapp.com/docs)
- [Architecture Overview](ARCHITECTURE.md)
- [Deployment Guide](DEPLOYMENT.md)

## 🤔 Questions?

- 💬 Join our [Discord server](https://discord.gg/your-server)
- 📧 Email us at dev@financeai.com
- 🐛 Open an issue for bugs
- 💡 Start a discussion for questions

---

Thank you for contributing to make personal finance management smarter and more accessible! 🙏