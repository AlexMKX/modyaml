import os
import shutil
from setuptools.command.build_py import build_py
from setuptools import setup


class CustomBuildPy(build_py):
    def run(self):
        # First run the standard build_py
        build_py.run(self)
        
        # Then copy readme.md to the package directory
        if os.path.exists('readme.md'):
            # Get the build directory
            build_dir = os.path.join(self.build_lib, 'modyaml')
            os.makedirs(build_dir, exist_ok=True)
            
            # Copy the file
            shutil.copy('readme.md', os.path.join(build_dir, 'readme.md'))
            print(f"Copied readme.md to {build_dir}")


setup(
    cmdclass={
        'build_py': CustomBuildPy,
    },
) 