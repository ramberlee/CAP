import os

legacy_dir = 'src/scenes/legacy'
for filename in os.listdir(legacy_dir):
    if filename.endswith('.tsx'):
        path = os.path.join(legacy_dir, filename)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        original = content

        # Fix imports
        content = content.replace("from './SceneWrapper'", "from '../SceneWrapper'")
        content = content.replace("from '../components/", "from '../../components/")
        content = content.replace("from '../styles/", "from '../../styles/")
        content = content.replace("from './types'", "from '../types'")

        if content != original:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed {filename}")

print("All legacy files fixed!")
