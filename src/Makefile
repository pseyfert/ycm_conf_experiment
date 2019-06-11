lib.so: jsonhandler.go
	go build -buildmode c-shared -o py_cc2ce.so .

clean:
	rm -f *.h lib.so

.PHONY: clean
