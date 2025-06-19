import os
from dotenv import load_dotenv
load_dotenv()
import json
from typing import Dict, List, Any
import google.generativeai as genai

class ReadmeGenerator:
    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY')
        print("Loaded GEMINI_API_KEY:", api_key)
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def generate_readme(self, github_url) -> str:
        from github_parser import GitHubParser
        parser = GitHubParser(github_url)
        repo_data = parser.get_repo_data()
        return self.generate_readme_content(repo_data)

    def analyze_repo_structure(self, repo_data: Dict) -> Dict[str, Any]:
        files = repo_data.get('files', {})
        categorized = {
            'config_files': [],
            'main_files': [],
            'frontend_files': [],
            'backend_files': [],
            'test_files': [],
            'documentation': [],
            'assets': []
        }
        for file_path, file_info in files.items():
            # SKIP node_modules files
            if "node_modules/" in file_path.replace("\\", "/"):
                continue
            if file_info.get('type') != 'file':
                continue
            ext = os.path.splitext(file_path)[-1].lower()
            # You can tune these lists as needed
            if ext in ['.json', '.yml', '.yaml', '.env', '.lock', '.conf', '.ini'] or 'config' in file_path.lower():
                categorized['config_files'].append(file_path)
            elif ext in ['.js', '.jsx', '.ts', '.tsx']:
                categorized['main_files'].append(file_path)
            elif ext in ['.css', '.scss', '.sass', '.less', '.html', '.htm']:
                categorized['frontend_files'].append(file_path)
            elif ext in ['.py', '.java', '.php', '.rb', '.go', '.rs']:
                categorized['backend_files'].append(file_path)
            elif ext in ['.md'] or any(name in file_path.lower() for name in ['readme', 'changelog', 'contributing', 'license']):
                categorized['documentation'].append(file_path)
            elif ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.pdf', '.doc', '.docx']:
                categorized['assets'].append(file_path)
            elif ext in ['.test.js', '.test.ts', '.spec.js', '.spec.ts']:
                categorized['test_files'].append(file_path)
        return categorized

    def extract_dependencies(self, files: Dict) -> Dict[str, List[str]]:
        dependencies = {'npm': [], 'pip': [], 'other': []}
        package_json_files = [f for f in files.keys() if f.endswith('package.json')]
        for file_path in package_json_files:
            try:
                content = files[file_path].get('content', '')
                if content:
                    package_data = json.loads(content)
                    deps = package_data.get('dependencies', {})
                    dev_deps = package_data.get('devDependencies', {})
                    dependencies['npm'].extend(list(deps.keys()) + list(dev_deps.keys()))
            except Exception as e:
                print(f"Error parsing {file_path}: {e}")
        req_files = [f for f in files.keys() if f.endswith('requirements.txt')]
        for file_path in req_files:
            try:
                content = files[file_path].get('content', '')
                if content:
                    deps = [line.split('==')[0].split('>=')[0].split('<=')[0]
                           for line in content.split('\n') if line.strip() and not line.startswith('#')]
                    dependencies['pip'].extend(deps)
            except Exception as e:
                print(f"Error parsing {file_path}: {e}")
        return dependencies

    def generate_readme_content(self, repo_data: Dict) -> str:
        categorized_files = self.analyze_repo_structure(repo_data)
        dependencies = self.extract_dependencies(repo_data['files'])
        key_files = self._get_key_file_contents(repo_data['files'], categorized_files)
        context = {
            'repo_name': repo_data.get('name', 'Unknown'),
            'description': repo_data.get('description', ''),
            'language': repo_data.get('language', 'Multiple'),
            'file_structure': categorized_files,
            'dependencies': dependencies,
            'file_count': len(repo_data.get('files', {})),
            'key_files': key_files
        }

        # Print all key file names (but do not include their contents anywhere)
        print("\n========= KEY FILES ANALYZED =========")
        for file_path in key_files:
            print(file_path)
        print("======================================\n")

        prompt = self._create_readme_prompt(context)
        try:
            response = self.model.generate_content(prompt)
            print("Gemini AI generated README.")
            return response.text
        except Exception as e:
            print("Gemini AI error:", e)
            return self._generate_fallback_readme(context)

    def _get_key_file_contents(self, files: Dict, categorized: Dict) -> Dict:
        key_contents = {}
        max_length = 3000

        # Always include package.json if present (anywhere in the repo, but not in node_modules)
        for fp in files:
            if "node_modules/" in fp.replace("\\", "/"):
                continue
            if fp.endswith('package.json'):
                content = files[fp].get('content', '')
                if content:
                    key_contents[fp] = content[:max_length] + ("\n... (truncated)" if len(content) > max_length else "")
                break  # only the first package.json

        # Include all .js, .jsx, .ts, .tsx, .py, .txt files (avoid duplicates, skip node_modules)
        for fp, finfo in files.items():
            if "node_modules/" in fp.replace("\\", "/"):
                continue
            ext = os.path.splitext(fp)[-1].lower()
            if ext in {'.js', '.jsx', '.ts', '.tsx', '.py', '.txt'} and fp not in key_contents:
                content = finfo.get('content', '')
                if content:
                    key_contents[fp] = content[:max_length] + ("\n... (truncated)" if len(content) > max_length else "")

        # Include README files (any .md with 'readme' in name, case-insensitive, skip node_modules)
        for fp, finfo in files.items():
            if "node_modules/" in fp.replace("\\", "/"):
                continue
            lower_fp = fp.lower()
            if (lower_fp.endswith('readme.md') or 'readme' in lower_fp) and fp not in key_contents:
                content = finfo.get('content', '')
                if content:
                    key_contents[fp] = content[:max_length] + ("\n... (truncated)" if len(content) > max_length else "")

        return key_contents

    def _create_readme_prompt(self, context: Dict) -> str:
        file_structure = "\n".join([
            f"**{category.replace('_', ' ').title()}:** {', '.join(files[:5])}" +
            (f" (+{len(files)-5} more)" if len(files) > 5 else "")
            for category, files in context['file_structure'].items() if files
        ])
        dependencies_info = "\n".join([
            f"**{dep_type.upper()}:** {', '.join(deps[:10])}" +
            (f" (+{len(deps)-10} more)" if len(deps) > 10 else "")
            for dep_type, deps in context['dependencies'].items() if deps
        ])
        # Do NOT include key file contents in the prompt
        prompt = f"""
Generate a comprehensive and professional README.md for a GitHub repository with the following information:

**File Structure:**
{file_structure}

**Dependencies:**
{dependencies_info}

Please generate a README.md that includes:
1. A compelling project title, badges and description
2. A watch demo link or Live website link option
3. Features list based on the code analysis
4. Technology stack
5. Project structure explanation
6. Usage examples
7. Installation instructions based on the dependencies
8. Contributing guidelines
9. License information

Make it professional, engaging, and developer-friendly. Use proper markdown formatting with emojis, badges, and clear sections. Infer the project's purpose and functionality from the code structure and dependencies.
"""
        return prompt
    
    def _generate_fallback_readme(self, context: Dict) -> str:
        """Generate a basic README if AI fails"""
        
        # Determine project type based on files
        project_type = "Application"
        if any('react' in dep.lower() for deps in context['dependencies'].values() for dep in deps):
            project_type = "React Application"
        elif any('flask' in dep.lower() for deps in context['dependencies'].values() for dep in deps):
            project_type = "Flask Application"
        elif any('express' in dep.lower() for deps in context['dependencies'].values() for dep in deps):
            project_type = "Express.js Application"
        
        readme_content = f"""# {context['repo_name']}

## 📝 Description
{context['description'] or f"A {project_type} built with {context['language']}"}

## 🚀 Features
- Modern {context['language']} application
- Well-structured codebase with {context['file_count']} files
- Professional development setup

## 🛠️ Installation

### Prerequisites
- Node.js (if using npm dependencies)
- Python (if using pip dependencies)

### Setup
1. Clone the repository
```bash
git clone <repository-url>
cd {context['repo_name']}
```

2. Install dependencies
"""
        
        if context['dependencies']['npm']:
            readme_content += """
```bash
npm install
```
"""
        
        if context['dependencies']['pip']:
            readme_content += """
```bash
pip install -r requirements.txt
```
"""
        
        readme_content += """
## 📁 Project Structure
```
"""
        
        for category, files in context['file_structure'].items():
            if files:
                readme_content += f"{category.replace('_', ' ').title()}: {len(files)} files\n"
        
        readme_content += """```

## 🤝 Contributing
1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📄 License
This project is licensed under the MIT License.
"""
        
        return readme_content
