package main

import (
	"C"
	"fmt"

	"github.com/pseyfert/compilecommands_to_compilerexplorer/cc2ce"
)

func outconvert(s string) *C.char {
	return C.CString(s)
}

//export GETDB
func GETDB(cpath *C.char) *C.char {
	gopath := C.GoString(cpath)

	json, err := cc2ce.JsonTUsByFilename(gopath)
	if err != nil {
		fmt.Printf("ERROR: %v\n", err)
		return outconvert("")
	}
	incs, err := cc2ce.IncludesFromJsonByDB(json, true)
	if err != nil {
		fmt.Printf("ERROR: %v\n", err)
		return outconvert("")
	}
	opts := ""
	for k, _ := range incs {
		opts += "-I"
		opts += k
		opts += " "
	}
	optsadd, err := cc2ce.OptionsFromJsonByDB(json) // spacesep
	if err != nil {
		fmt.Printf("ERROR: %v\n", err)
		return outconvert("")
	}
	opts = opts + optsadd

	return outconvert(opts)
}

//export GETOPTS
func GETOPTS(cpath *C.char) *C.char {
	gopath := C.GoString(cpath)

	json, err := cc2ce.JsonTUsByFilename(gopath)
	if err != nil {
		fmt.Printf("ERROR: %v\n", err)
		return outconvert("")
	}
	opts, err := cc2ce.OptionsFromJsonByDB(json) // spacesep
	if err != nil {
		fmt.Printf("ERROR: %v\n", err)
		return outconvert("")
	}

	return outconvert(opts)
}

//export GETINCS
func GETINCS(cpath *C.char) *C.char {
	gopath := C.GoString(cpath)

	json, err := cc2ce.JsonTUsByFilename(gopath)
	if err != nil {
		fmt.Printf("ERROR: %v\n", err)
		return outconvert("")
	}
	incs, err := cc2ce.IncludesFromJsonByDB(json, true)
	if err != nil {
		fmt.Printf("ERROR: %v\n", err)
		return outconvert("")
	}
	opts := ""
	for k, _ := range incs {
		opts += k
		opts += " "
	}

	return outconvert(opts)
}

func main() {
}
