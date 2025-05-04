from setuptools import setup, find_packages
from typing import List

def get_requirements(file_path:str) -> List[str]:
    
    '''
    This function is used for fetchinng the requirement list 
    '''
    DOT = '-e .'
    requirements = []
    with open(file_path) as file_obj:
        requirements = file_obj.readlines()
        requirements = [req.replace("\n", " ") for req in requirements]
        
        if DOT in requirements:
            requirements.remove(DOT)
    
    return requirements


setup(
    name='Ecommerce_Pricing_Ai',
    version='0.0.001',
    author='Naman',
    author_email='namankumar4499@gmail.com',
    packages=find_packages(),
    install_requires=get_requirements('requirements.txt')
    
)