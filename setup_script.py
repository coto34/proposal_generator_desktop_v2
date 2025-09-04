#!/usr/bin/env python3
"""
Enhanced Proposal Generator - Setup and Validation Script
=========================================================

This script validates your environment, checks dependencies, and helps configure
the enhanced proposal generator with robust error handling and improved workflow.

Run this script before using the main application to ensure everything is properly configured.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any


def print_header(title: str):
    """Print formatted header"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def print_section(title: str):
    """Print formatted section"""
    print(f"\n📋 {title}")
    print("-" * 40)


def print_success(message: str):
    """Print success message"""
    print(f"✅ {message}")


def print_warning(message: str):
    """Print warning message"""
    print(f"⚠️  {message}")


def print_error(message: str):
    """Print error message"""
    print(f"❌ {message}")


def print_info(message: str):
    """Print info message"""
    print(f"ℹ️  {message}")


class SetupValidator:
    """Enhanced setup validator for the proposal generator"""
    
    def __init__(self):
        self.results = {
            "python_version": None,
            "dependencies": {},
            "api_keys": {},
            "directory_structure": {},
            "file_validation": {},
            "recommendations": []
        }
    
    def run_full_validation(self) -> Dict[str, Any]:
        """Run complete validation suite"""
        print_header("PROPOSAL GENERATOR - ENHANCED SETUP VALIDATION")
        print("🚀 Validating enhanced workflow configuration...")
        
        # Step 1: Python version
        self.validate_python_version()
        
        # Step 2: Dependencies
        self.validate_dependencies()
        
        # Step 3: Directory structure
        self.validate_directory_structure()
        
        # Step 4: Core files
        self.validate_core_files()
        
        # Step 5: API keys
        self.validate_api_configuration()
        
        # Step 6: Generate recommendations
        self.generate_recommendations()
        
        # Step 7: Summary and report
        self.print_summary()
        self.save_validation_report()
        
        return self.results
    
    def validate_python_version(self):
        """Validate Python version"""
        print_section("Python Version Check")
        
        version = sys.version_info
        version_str = f"{version.major}.{version.minor}.{version.micro}"
        
        self.results["python_version"] = {
            "version": version_str,
            "major": version.major,
            "minor": version.minor,
            "supported": version >= (3, 8)
        }
        
        if version >= (3, 8):
            print_success(f"Python {version_str} (✓ Supported)")
        else:
            print_error(f"Python {version_str} (✗ Requires Python 3.8+)")
            self.results["recommendations"].append(
                "Upgrade to Python 3.8 or higher for optimal compatibility"
            )
    
    def validate_dependencies(self):
        """Validate required and optional dependencies"""
        print_section("Dependency Validation")
        
        # Core dependencies
        core_deps = [
            ("tkinter", "tkinter", "GUI framework (usually built-in)"),
            ("requests", "requests", "HTTP requests for API calls"),
            ("python-dotenv", "dotenv", "Environment configuration"),
            ("pathlib", "pathlib", "Path handling (built-in)"),
            ("json", "json", "JSON processing (built-in)")
        ]
        
        # Document processing dependencies
        doc_deps = [
            ("pypdf", "pypdf", "PDF text extraction"),
            ("python-docx", "docx", "Word document processing"),
            ("pdfminer.six", "pdfminer", "Advanced PDF processing"),
            ("docxtpl", "docxtpl", "Word template processing"),
            ("openpyxl", "openpyxl", "Excel file generation")
        ]
        
        # Optional dependencies
        optional_deps = [
            ("pydantic", "pydantic", "Data validation"),
            ("loguru", "loguru", "Enhanced logging")
        ]
        
        self.results["dependencies"] = {
            "core": self._check_dependency_group(core_deps, "Core Dependencies"),
            "document_processing": self._check_dependency_group(doc_deps, "Document Processing"),
            "optional": self._check_dependency_group(optional_deps, "Optional Dependencies")
        }
    
    def _check_dependency_group(self, deps: List[Tuple[str, str, str]], group_name: str) -> Dict[str, Any]:
        """Check a group of dependencies"""
        print(f"\n📦 {group_name}:")
        
        group_results = {}
        for package_name, import_name, description in deps:
            try:
                __import__(import_name)
                print_success(f"{package_name}: Available")
                group_results[package_name] = {
                    "available": True,
                    "description": description,
                    "import_name": import_name
                }
            except ImportError:
                print_warning(f"{package_name}: Missing - {description}")
                group_results[package_name] = {
                    "available": False,
                    "description": description,
                    "import_name": import_name,
                    "install_command": f"pip install {package_name}"
                }
        
        return group_results
    
    def validate_directory_structure(self):
        """Validate project directory structure"""
        print_section("Directory Structure")
        
        required_dirs = [
            ("services", "Core service modules"),
            ("ui", "User interface components"),
            ("validation", "Data validation schemas"),
            ("runs", "Output directory for generated proposals"),
            ("runs/state", "Application state storage")
        ]
        
        optional_dirs = [
            ("templates", "Document templates"),
            ("logs", "Application logs"),
            ("backups", "Configuration backups")
        ]
        
        self.results["directory_structure"] = {
            "required": {},
            "optional": {}
        }
        
        print("📁 Required directories:")
        for dir_name, description in required_dirs:
            dir_path = Path(dir_name)
            exists = dir_path.exists()
            
            if exists:
                print_success(f"{dir_name}/ - {description}")
            else:
                print_warning(f"{dir_name}/ - {description} (Missing)")
                # Create missing directories
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    print_info(f"Created directory: {dir_name}/")
                except Exception as e:
                    print_error(f"Could not create directory {dir_name}/: {e}")
            
            self.results["directory_structure"]["required"][dir_name] = {
                "exists": exists,
                "description": description,
                "created": not exists  # Track if we created it
            }
        
        print("\n📁 Optional directories:")
        for dir_name, description in optional_dirs:
            dir_path = Path(dir_name)
            exists = dir_path.exists()
            
            if exists:
                print_success(f"{dir_name}/ - {description}")
            else:
                print_info(f"{dir_name}/ - {description} (Optional)")
            
            self.results["directory_structure"]["optional"][dir_name] = {
                "exists": exists,
                "description": description
            }
    
    def validate_core_files(self):
        """Validate core application files"""
        print_section("Core Files Validation")
        
        core_files = [
            ("app.py", "Main application entry point"),
            ("services/__init__.py", "Services package"),
            ("services/llm_providers.py", "LLM API clients"),
            ("services/document_processor.py", "Document processing"),
            ("services/token_manager.py", "Token and chunking management"),
            ("ui/wizard.py", "Main UI wizard"),
            ("ui/components.py", "UI components"),
            ("validation/schemas.py", "Data validation schemas"),
            ("requirements.txt", "Python dependencies"),
        ]
        
        config_files = [
            (".env", "Environment configuration (API keys)"),
            (".gitignore", "Git ignore rules")
        ]
        
        self.results["file_validation"] = {
            "core_files": {},
            "config_files": {}
        }
        
        print("📄 Core application files:")
        for file_path, description in core_files:
            path_obj = Path(file_path)
            exists = path_obj.exists()
            
            if exists:
                # Check file size and basic content
                size = path_obj.stat().st_size
                print_success(f"{file_path} - {description} ({size} bytes)")
                
                self.results["file_validation"]["core_files"][file_path] = {
                    "exists": True,
                    "size_bytes": size,
                    "description": description
                }
            else:
                print_error(f"{file_path} - {description} (Missing)")
                self.results["file_validation"]["core_files"][file_path] = {
                    "exists": False,
                    "description": description
                }
        
        print("\n📄 Configuration files:")
        for file_path, description in config_files:
            path_obj = Path(file_path)
            exists = path_obj.exists()
            
            if exists:
                print_success(f"{file_path} - {description}")
                self.results["file_validation"]["config_files"][file_path] = {
                    "exists": True,
                    "description": description
                }
            else:
                print_warning(f"{file_path} - {description} (Missing)")
                self.results["file_validation"]["config_files"][file_path] = {
                    "exists": False,
                    "description": description
                }
                
                if file_path == ".env":
                    self._create_env_template()
    
    def _create_env_template(self):
        """Create .env template file"""
        env_template = """# Proposal Generator - Environment Configuration
# Copy this file to .env and fill in your API keys

# DeepSeek API Configuration (for narrative generation)
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# Anthropic Claude API Configuration (for budget generation)
SONNET_API_KEY=your_anthropic_api_key_here
# Alternative name for the same key:
# ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Optional: Custom API endpoints (advanced users only)
# DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
# SONNET_BASE_URL=https://api.anthropic.com/v1

# Application Configuration
# LOG_LEVEL=INFO
# OUTPUT_DIRECTORY=runs
"""
        
        try:
            with open(".env.template", "w", encoding="utf-8") as f:
                f.write(env_template)
            print_info("Created .env.template - copy to .env and add your API keys")
        except Exception as e:
            print_error(f"Could not create .env template: {e}")
    
    def validate_api_configuration(self):
        """Validate API key configuration"""
        print_section("API Configuration")
        
        # Try to load .env file
        try:
            from dotenv import load_dotenv
            load_dotenv()
            print_success("Environment file loaded")
        except ImportError:
            print_warning("python-dotenv not available - install with: pip install python-dotenv")
        except Exception as e:
            print_warning(f"Could not load .env file: {e}")
        
        # Check API keys
        api_keys = {
            "DEEPSEEK_API_KEY": {
                "description": "DeepSeek API key for narrative generation",
                "required": True
            },
            "SONNET_API_KEY": {
                "description": "Anthropic Claude API key for budget generation", 
                "required": True
            },
            "ANTHROPIC_API_KEY": {
                "description": "Alternative name for Anthropic Claude API key",
                "required": False
            }
        }
        
        self.results["api_keys"] = {}
        
        for key_name, config in api_keys.items():
            key_value = os.getenv(key_name)
            has_key = key_value is not None and key_value.strip() != ""
            
            self.results["api_keys"][key_name] = {
                "configured": has_key,
                "description": config["description"],
                "required": config["required"],
                "length": len(key_value) if key_value else 0
            }
            
            if has_key:
                # Mask the key for security
                masked_key = key_value[:8] + "..." + key_value[-4:] if len(key_value) > 12 else "***"
                print_success(f"{key_name}: Configured ({masked_key})")
            else:
                status = "Required" if config["required"] else "Optional"
                print_warning(f"{key_name}: Not configured ({status})")
        
        # Special check for Anthropic key alternatives
        has_anthropic = (os.getenv("SONNET_API_KEY") or os.getenv("ANTHROPIC_API_KEY"))
        if not has_anthropic:
            self.results["recommendations"].append(
                "Configure either SONNET_API_KEY or ANTHROPIC_API_KEY for budget generation"
            )
    
    def generate_recommendations(self):
        """Generate setup recommendations"""
        print_section("Recommendations")
        
        recommendations = []
        
        # Check missing dependencies
        missing_core = [
            pkg for pkg, info in self.results["dependencies"]["core"].items() 
            if not info["available"]
        ]
        
        if missing_core:
            install_cmd = "pip install " + " ".join(missing_core)
            recommendations.append(f"Install missing core dependencies: {install_cmd}")
        
        missing_doc = [
            pkg for pkg, info in self.results["dependencies"]["document_processing"].items()
            if not info["available"]
        ]
        
        if missing_doc:
            install_cmd = "pip install " + " ".join(missing_doc)
            recommendations.append(f"Install document processing dependencies: {install_cmd}")
        
        # Check missing files
        missing_core_files = [
            file for file, info in self.results["file_validation"]["core_files"].items()
            if not info["exists"]
        ]
        
        if missing_core_files:
            recommendations.append("Some core files are missing - ensure you have the complete codebase")
        
        # Check API configuration
        if not self.results["api_keys"].get("DEEPSEEK_API_KEY", {}).get("configured"):
            recommendations.append("Configure DEEPSEEK_API_KEY in .env file for narrative generation")
        
        anthropic_configured = (
            self.results["api_keys"].get("SONNET_API_KEY", {}).get("configured") or
            self.results["api_keys"].get("ANTHROPIC_API_KEY", {}).get("configured")
        )
        
        if not anthropic_configured:
            recommendations.append("Configure SONNET_API_KEY or ANTHROPIC_API_KEY in .env file for budget generation")
        
        # Add existing recommendations
        recommendations.extend(self.results["recommendations"])
        
        self.results["recommendations"] = recommendations
        
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                print(f"{i}. {rec}")
        else:
            print_success("No issues found! Your setup looks good.")
    
    def print_summary(self):
        """Print validation summary"""
        print_section("Validation Summary")
        
        # Count statuses
        core_deps_ok = sum(1 for info in self.results["dependencies"]["core"].values() if info["available"])
        total_core_deps = len(self.results["dependencies"]["core"])
        
        doc_deps_ok = sum(1 for info in self.results["dependencies"]["document_processing"].values() if info["available"])
        total_doc_deps = len(self.results["dependencies"]["document_processing"])
        
        core_files_ok = sum(1 for info in self.results["file_validation"]["core_files"].values() if info["exists"])
        total_core_files = len(self.results["file_validation"]["core_files"])
        
        api_keys_ok = sum(1 for info in self.results["api_keys"].values() if info["configured"] and info["required"])
        total_required_keys = sum(1 for info in self.results["api_keys"].values() if info["required"])
        
        print(f"🐍 Python Version: {'✅' if self.results['python_version']['supported'] else '❌'} {self.results['python_version']['version']}")
        print(f"📦 Core Dependencies: {'✅' if core_deps_ok == total_core_deps else '⚠️'} {core_deps_ok}/{total_core_deps}")
        print(f"📚 Document Processing: {'✅' if doc_deps_ok >= total_doc_deps//2 else '⚠️'} {doc_deps_ok}/{total_doc_deps}")
        print(f"📄 Core Files: {'✅' if core_files_ok == total_core_files else '❌'} {core_files_ok}/{total_core_files}")
        print(f"🔑 API Keys: {'✅' if api_keys_ok == total_required_keys else '❌'} {api_keys_ok}/{total_required_keys}")
        print(f"📋 Recommendations: {len(self.results['recommendations'])}")
        
        # Overall status
        critical_issues = (
            not self.results['python_version']['supported'] or
            core_deps_ok < total_core_deps or
            core_files_ok < total_core_files or
            api_keys_ok < total_required_keys
        )
        
        if critical_issues:
            print_error("❌ Setup has critical issues - please address recommendations")
        elif self.results['recommendations']:
            print_warning("⚠️ Setup is functional but has some recommendations")
        else:
            print_success("✅ Setup is complete and ready!")
    
    def save_validation_report(self):
        """Save detailed validation report"""
        try:
            report_path = Path("runs") / f"setup_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            # Add metadata
            self.results["metadata"] = {
                "validation_time": datetime.now().isoformat(),
                "script_version": "2.0.0",
                "python_executable": sys.executable,
                "working_directory": str(Path.cwd())
            }
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
            
            print_info(f"Detailed report saved: {report_path}")
            
        except Exception as e:
            print_warning(f"Could not save validation report: {e}")


def install_missing_dependencies():
    """Interactive dependency installation"""
    print_header("DEPENDENCY INSTALLATION")
    
    validator = SetupValidator()
    validator.validate_dependencies()
    
    # Collect missing dependencies
    missing_deps = []
    for group_name, group_deps in validator.results["dependencies"].items():
        for pkg_name, pkg_info in group_deps.items():
            if not pkg_info["available"]:
                missing_deps.append((pkg_name, pkg_info.get("install_command", f"pip install {pkg_name}"), group_name))
    
    if not missing_deps:
        print_success("All dependencies are already installed!")
        return True
    
    print(f"Found {len(missing_deps)} missing dependencies:")
    for pkg_name, install_cmd, group in missing_deps:
        print(f"  • {pkg_name} ({group})")
    
    # Ask user if they want to install
    try:
        response = input("\nWould you like to install missing dependencies? (y/n): ").strip().lower()
        if response not in ['y', 'yes']:
            print("Skipping dependency installation.")
            return False
        
        print("\n🔧 Installing dependencies...")
        
        for pkg_name, install_cmd, group in missing_deps:
            print(f"\nInstalling {pkg_name}...")
            try:
                result = subprocess.run(install_cmd.split(), capture_output=True, text=True)
                if result.returncode == 0:
                    print_success(f"Installed {pkg_name}")
                else:
                    print_error(f"Failed to install {pkg_name}: {result.stderr}")
            except Exception as e:
                print_error(f"Error installing {pkg_name}: {e}")
        
        print_success("Dependency installation completed!")
        return True
        
    except KeyboardInterrupt:
        print("\nInstallation cancelled by user.")
        return False


def test_api_connections():
    """Test API connections"""
    print_header("API CONNECTION TESTING")
    
    try:
        from services.llm_providers import create_test_clients
        
        print_info("Testing API connections...")
        test_results = create_test_clients()
        
        for provider, result in test_results.items():
            print(f"\n🔌 {provider.title()} API:")
            if result["available"]:
                print_success(f"Connection successful")
                if result.get("working_model"):
                    print_info(f"Using model: {result['working_model']}")
            else:
                print_error(f"Connection failed: {result.get('error', 'Unknown error')}")
        
        return test_results
        
    except ImportError as e:
        print_error(f"Cannot test APIs - missing dependencies: {e}")
        return {}


def create_sample_project():
    """Create a sample project configuration"""
    print_header("SAMPLE PROJECT CREATION")
    
    sample_project = {
        "title": "Fortalecimiento de Capacidades Comunitarias para el Desarrollo Sostenible",
        "country": "Guatemala",
        "language": "es",
        "donor": "Agencia de Cooperación Internacional",
        "duration_months": "18",
        "budget_cap": "$150,000 USD",
        "coverage_type": "Municipal",
        "department": "Quetzaltenango",
        "municipality": "Salcajá",
        "target_population": "Comunidades indígenas rurales del municipio de Salcajá",
        "beneficiaries_direct": "500",
        "beneficiaries_indirect": "2000",
        "demographic_focus": "Pueblos indígenas",
        "org_profile": "IEPADES - Más de 30 años fortaleciendo capacidades locales en Guatemala"
    }
    
    try:
        sample_path = Path("runs/sample_project.json")
        with open(sample_path, 'w', encoding='utf-8') as f:
            json.dump(sample_project, f, ensure_ascii=False, indent=2)
        
        print_success(f"Sample project created: {sample_path}")
        print_info("You can load this sample in the application for testing")
        
    except Exception as e:
        print_error(f"Could not create sample project: {e}")


def main():
    """Main setup function"""
    print_header("ENHANCED PROPOSAL GENERATOR - SETUP WIZARD")
    print("🎯 This script will validate and configure your environment")
    
    try:
        # Step 1: Full validation
        validator = SetupValidator()
        results = validator.run_full_validation()
        
        # Step 2: Offer dependency installation
        if any(not info["available"] for group in results["dependencies"].values() for info in group.values()):
            install_missing_dependencies()
        
        # Step 3: Test API connections if keys are configured
        api_configured = any(info["configured"] for info in results["api_keys"].values())
        if api_configured:
            test_api_connections()
        
        # Step 4: Create sample project
        create_sample_project()
        
        # Final message
        print_header("SETUP COMPLETE")
        
        if not results["recommendations"]:
            print_success("🎉 Your environment is fully configured!")
            print_info("You can now run: python app.py")
        else:
            print_warning("⚠️ Setup completed with recommendations")
            print_info("Review the recommendations above before running the application")
            print_info("You can still try running: python app.py")
        
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print_error(f"Setup failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()