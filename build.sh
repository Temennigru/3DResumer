unameOut="$(uname -s)"
case "${unameOut}" in
    Linux*)     machine=linux;;
    Darwin*)    machine=mac;;
    *)          exit 1
esac

rm -r bin/$machine
rm -r build
rm resume.spec
pyinstaller --distpath bin/$machine --hidden-import PySimpleGUI -wF resume.py