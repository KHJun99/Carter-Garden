from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'follower'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # 런치 파일 등록
        (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*launch.[pxy][yma]*'))),
        # 월드 파일(.world) 등록
        (os.path.join('share', package_name, 'worlds'), glob(os.path.join('worlds', '*'))),
        # 설정 파일(.yaml) 등록
        (os.path.join('share', package_name, 'config'), glob(os.path.join('config', '*.yaml'))),
	# 모델 파일(.sdf) 등록
	(os.path.join('share', package_name, 'models', 'long_chair'), glob(os.path.join('models', 'long_chair', '*'))),
	(os.path.join('share', package_name, 'models', 'blue_shelf'), glob(os.path.join('models', 'blue_shelf', '*'))),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='gzero',
    maintainer_email='gzero@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
                'follower_node = follower.follower_node:main',
                'yolo_node = follower.yolo_node:main',
                'nav_follower_node = follower.nav_follower_node:main',
                # 자율주행 통합을 위한 navigator_node 미리 등록
                'navigator_node = follower.navigator_node:main'
        ],
    },
)
