# pythonista-c-utils

Utilities for working with `ctypes`/`objc_util`/`cffi` in Pythonista ~~1.6~~ 3.0.

## cffipp

`cffipp` is a library that provides a preprocessor for `cffi`.

### Installation

Requires Pythonista 3, Python 3, `ply` (tested with version 3.8), `pycparser` (tested with version 2.14) and `cffi` version 1.6.0 (this is likely an exact requirement, `cffipp` does some dark magic with `cffi`'s internals).

For anything meaningful you'll also need the iOS SDK header files. If you're on a Mac, the best way to get them is from Xcode. If you don't have it, it's free on the App Store, no registration of any kind required. Once it's installed, open your `Applications` folder, right-click `Xcode.app`and select "Show Package Contents". Go to `Contents/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS.sdk/usr`, zip up the `include` folder (right-click and select 'Compress "include"', the zip will land on your desktop) and get it into Pythonista somehow. Extract it and move the `include` folder into `cffipp`'s `include_private` folder and name it `usr_include`. (Or change the include path by editing `main.py`, if you prefer.) The header files require no additional modification.

If you're not on a Mac, there's no "official" way to get the headers. There are probably places where you can get them though. If you don't mind a big download and some work, you can also register your Apple ID for a free Apple Developer membership under https://developer.apple.com/, download the Xcode installation dmg file, and find the files using 7-Zip from http://7-zip.org/.

### Usage

To use, `import cffipp`, construct a `cffipp.CFFIPreprocessor`, tell it to `cdef`/`cdef_include` some things, then use the FFI (accessible through the preprocessor's `ffi` attribute) like you would normally.

