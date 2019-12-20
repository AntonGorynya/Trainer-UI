from cx_Freeze import setup, Executable


executables = [Executable('Trainer UI.py' , base="Win32GUI")]
#include_files = ['design.py', 'main.py', 'UI.py']



includes = ['pyexpat', 'idna.idnadata', 'xlwt.ExcelFormulaParser', 'xlwt.ExcelFormulaLexer', 'numpy', 'pandas']
options = {
    'build_exe': {
        'include_msvcr': True,
        "packages": ["os", "numpy" ,"xlwt"],
        'includes': includes,
    }
}



setup(name='hello_world',
      version='0.0.2',
      description='My Hello World App!',
      executables=executables,
      options=options)