# EmoLanguage Project Makefile
# ===========================

.PHONY: install clean test setup-dev help

# Default target
all: install

# Install all dependencies and setup NLTK data
install:
	@echo "Installing Python dependencies..."
	pip install -r requirements.txt
	@echo "Setting up NLTK data..."
	python -c "from lib.word_normalizer import WordNormalizer; WordNormalizer()"
	@echo "Installation complete!"

# Clean up temporary files and caches
clean:
	@echo "Cleaning temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".DS_Store" -delete 2>/dev/null || true
	@echo "Clean complete!"

# Run basic tests
test:
	@echo "Running basic functionality tests..."
	echo "Hello world" | python3 encode.py
	echo "👋🌍" | python3 decode.py
	@echo "Tests complete!"

# Development setup with additional tools
setup-dev: install
	@echo "Setting up development environment..."
	pip install pytest black isort mypy
	@echo "Development setup complete!"

# Show help
help:
	@echo "EmoLanguage Makefile"
	@echo "===================="
	@echo ""
	@echo "Available targets:"
	@echo "  install    - Install dependencies and setup NLTK data"
	@echo "  clean      - Remove temporary files and caches"
	@echo "  test       - Run basic functionality tests"
	@echo "  setup-dev  - Setup development environment"
	@echo "  help       - Show this help message"
	@echo ""
	@echo "Quick start:"
	@echo "  make install"
	@echo "  echo 'Hello world' | python3 encode.py"
