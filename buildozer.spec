[app]

# (str) Title of your application
title = PasswordManager

# (str) Package name
package.name = passwordmanager

# (str) Package domain (needed for android/ios packaging)
package.domain = org.russkiyokypant

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (do not include data folder if you want to keep it external)
source.include_exts = py,png,jpg,kv,atlas

# (list) List of inclusions using pattern matching
#source.include_patterns = assets/*, images/*.png

# (list) Source files to exclude (let empty to not exclude anything)
#source.exclude_exts = spec

# (list) List of directory names to not be packed
#source.exclude_dirs = tests, bin, docs, dist, .git, backups, data

# (list) List of exclusions using pattern matching
#source.exclude_patterns = license, images/*/*.jpg

# (str) Application versioning (method 1)
version = 1.0.0

# (str) Application versioning (method 2)
# version.regex = __version__ = ['"](.*)['"]
# version.filename = %(source.dir)s/main.py

# (list) Application requirements
#  !!  Убедитесь, что все зависимости перечислены
requirements = python3,kivy,cryptography,yadisk,python-dotenv,requests,pyotp

# (str) Custom source folders for requirements
# requirements.custom.sources = https://github.com/kivy/kivy

# (list) Garden requirements
#garden_requirements =

# (str) Presplash of the application
#presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon of the application
#icon.filename = %(source.dir)s/data/icon.png

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (list) List of service to declare
#services = NAME:ENTRYPOINT_TO_PY,NAME2:ENTRYPOINT2_TO_PY

#
# OS X Specific
#

#
# author = © Copyright Info

# change the major version of python used by the app
osx.python_version = 3

# Kivy version to use
osx.kivy_version = 1.11.1

#
# Android Specific
#

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (string) Presplash background color (for new android toolchain)
# android.presplash_color = #FFFFFF

# (list) Permissions
android.permissions = INTERNET,ACCESS_NETWORK_STATE,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

# (int) Android SDK version to use
android.sdk = 33

# (str) Android NDK version to use
android.ndk = 25b

# (int) Android NDK API to use. This is the minimum API your app will support, it should usually match android.minapi.
android.ndk_api = 21

# (bool) Use --private data storage (True) or --dir public storage (False)
#android.private_storage = True

# (str) Android Java directory where the java code is located
#android.add_src =

# (str) python-for-android branch to use, defaults to stable
#android.p4a_branch = develop

# (bool) If True, then openssl will be included in the build.
android.include_openssl = True

# (str) Android logcat filters to use
#android.logcat_filters = *:S python:D

# (bool) Copy lib instead of making a symlink when pushing to device
#android.copy_libs = 1

# (list) List of java .jar files to add to the libs so that pyjnius can access
# their classes. Don't add jars that you do not need, since can be package.
#android.add_src =

# (list) List of Java files to add to the project. These will not be compiled and added to the APK, but
# they are useful for importing classes from your app.
#android.add_src = /path/to/java/file.java

# (str) python-for-android branch to use, if not master, useful to try new features before release
#android.p4a_branch = develop

# (str) Android NDK directory (if empty, it will be automatically downloaded.)
#android.ndk_path =

# (str) Android SDK directory (if empty, it will be automatically downloaded.)
#android.sdk_path =

# (str) ANT directory (if empty, it will be automatically downloaded.)
#android.ant_path =

# (bool) If True, then skip trying to update the Android sdk
#android.skip_update = False

# (bool) If True, then bypass compiling the Python/Java files
#android.ignore_setup = False

# (int) Version code to use for the application (will be used if version is not set)
#android.version_code = 1

# (str) Android application category, e.g. 'Travel'
#android.category =

# (str) The Android app theme. The default is 'Theme.Material.Light'. 
# See: https://developer.android.com/reference/android/R.style for a list of available themes.
#android.theme = Theme.Material.Light

# (bool) Enable Android packaging for Google Play Store (build with --release)
#android.playstore = True

# (bool) Enable Android packaging for Amazon App Store (build with --release)
#android.amazon = True

# (bool) Enable/disable Android packaging for HUAWEI AppGallery (build with --release)
#android.huawei = True

#
# Python for android (p4a) specific
#

# (str) python-for-android git clone directory (if empty, it will be automatically cloned from github)
#android.p4a_source_dir =

# (str) The directory in which python-for-android should look for your own build recipes (if any)
#android.p4a_local_recipes =

# (str) The directory in which python-for-android should store downloaded dependencies
#android.p4a_cache_dir =

# (bool) If True, use the selected p4a branch even if the p4a directory already exists
#android.p4a_force_branch = False

# (bool) If True, try to download the prebuilt APK from the server (for debugging)
#android.p4a_prebuilt = False

# (bool) If True, build with the debug mode (for debugging)
#android.debug = True

# (list) List of Android architectures to build for, e.g. armeabi-v7a, arm64-v8a
#android.arch = armeabi-v7a, arm64-v8a

# (bool) If True, compile the Python code to .pyo (not recommended for APK)
#android.compile_pyo = False

#
# iOS Specific
#

# (str) Path to a custom kivy-ios folder
#ios.kivy_ios_dir = ../kivy-ios

# (str) Path to the iOS SDK (if empty, it will be automatically downloaded)
#ios.sdk_path =

# (str) Path to the iOS toolchain (if empty, it will be automatically downloaded)
#ios.toolchain_path =

# (bool) If True, use the Xcode development team for signing
#ios.use_xcode_dev_team = False

# (str) Xcode development team ID
#ios.dev_team = 123ABC456

# (str) Xcode provisioning profile
#ios.profile = path/to/profile

# (str) Xcode provisioning profile UUID
#ios.profile_uuid = 12345678-1234-1234-1234-123456789012

# (str) iOS deployment target
#ios.deployment_target = 13.0

# (str) iOS bundle identifier
#ios.bundle_identifier = com.example.myapp

# (bool) Enable iOS app signing
#ios.codesign = True

# (str) iOS app signing identity
#ios.codesign_identity =

#
# Features
#

# (list) List of features (see also https://github.com/kivy/kivy/wiki/Kivy-Android-Integration)
#android.features = android.hardware.location, android.hardware.location.gps

# (list) List of services (see also https://github.com/kivy/kivy/wiki/Kivy-Android-Integration)
#android.services = myservice:path/to/service.py

#
# (list) A list of strings representing the files/dirs to copy to the application bundle
#android.add_src = /path/to/file.java, /path/to/dir/

# (bool) If True, the application will be deployed as a portable package
#android.portable = False

# (bool) If True, the application will be packaged for the Google Play Store
#android.playstore = False

# (bool) If True, the application will be packaged for the Amazon App Store
#android.amazon = False

# (bool) If True, the application will be packaged for the HUAWEI AppGallery
#android.huawei = False

# (list) List of additional Java classes to include in the APK
#android.add_java_src =

# (list) List of additional Java libraries to include in the APK (as .jar files)
#android.add_jar =

# (list) List of additional Java libraries to include in the APK (as .aar files)
#android.add_aar =

# (list) List of additional Java libraries to include in the APK (as .so files)
#android.add_libs_armeabi_v7a =
#android.add_libs_arm64_v8a =

# (list) List of additional assets to include in the APK
#android.add_assets =

#
# Tag for buildozer (do not change this line)
# tag: buildozer, version: 1.0.0