import cffipp

if __name__ == "__main__":
	pp = cffipp.CFFIPreprocessor()
	pp.cdef_include("objc/objc.h")
	pp.cdef_include("CoreFoundation/CoreFoundation.h", once=True)

