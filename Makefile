run: build/azureblur.so
	python azureblur.py

OBJS = build/Blur.o build/azureblur.o

build/azureblur.so: ${OBJS} Makefile
	g++ -shared -o $@ ${OBJS}

build/%.o: src/%.cpp Makefile
	g++ $< -o $@ -I src -c -fPIC

clean:
	rm build/*
