import check_bin as _

from os import system, mkdir, listdir
from os.path import isfile
from sys import argv
from shutil import copy, copytree
from concurrent.futures import ThreadPoolExecutor

system("cls")

if "-y" not in argv:
    if input("Sure? (y/n) ").lower() not in ("yes", "y"):
        raise SystemExit

def compile(file: str, hideconsole: bool):
    system(f"{pyi_makespec} \"{file}\" -i icon.ico {"-w" if hideconsole and not debug else ""}")
    spec = f"{file.replace('.py', '')}.spec"
    with open(spec, "r", encoding="utf-8") as f:
        spec_data = f.read()
    with open(spec, "w", encoding="utf-8") as f:
        f.write(extend + spec_data)
    system(f"{pyinstaller} \"{spec}\"")
    system(f"del {file.replace(".py", ".spec")}")

debug = "--debug" in argv
compile_files = [
    ("main.py", False),
    ("tk_launcher.py", False),
    ("phigros.py", False),
    *(map(lambda x: (x, False), filter(lambda x: (
        x.startswith("tool-")
        and x.endswith(".py")
        and x not in (
            "tool-pack.py",
            "tool-create-innosetup-config.py"
        )
    ), listdir())))
]
res_files = [
    "_internal",
    "bin", "lib",
    "resources", "shaders",
    "7z.dll", "7z.exe",
    "ecwv_installer.exe",
    "icon.ico",
    "libogg.dll", "libvorbis.dll",
    "web_canvas.html"
]
extend = open("_compile_pyiextend.py", "r", encoding="utf-8").read()

system("python -m venv compile_venv")
py = ".\\compile_venv\\Scripts\\python.exe"

system(f"{py} -m pip install --upgrade pip")
system(f"{py} -m pip install -r .\\requirements.txt")
system(f"{py} -m pip install pyinstaller")

pyinstaller = ".\\compile_venv\\Scripts\\pyinstaller.exe"
pyi_makespec = ".\\compile_venv\\Scripts\\pyi-makespec.exe"

executor = ThreadPoolExecutor(max_workers=6)

for future in [executor.submit(compile, file, hideconsole) for file, hideconsole in compile_files]:
    future.result()

for file, _ in compile_files:
    system(f"xcopy \".\\dist\\{file.replace(".py", "")}\\*\" .\\ /c /q /e /y")

system("rmdir .\\compile_venv /s /q")
system("rmdir .\\build /s /q")
system("rmdir .\\dist /s /q")

if "--zip" in argv:
    _copy = lambda src, tar: copy(src, tar) if isfile(src) else copytree(src, f"{tar}\\{src}")
    try: mkdir(".\\compile_result")
    except FileExistsError: pass
    for i, _ in compile_files:
        _copy(i.replace(".py", ".exe"), ".\\compile_result")
    for i in res_files:
        _copy(i, ".\\compile_result")
    system("7z a compile_result.zip .\\compile_result\\*")

print("\nCompile complete!")
system("pause")
