PORT    := /dev/ttyUSB0
SRC     := .
SRCS    := $(wildcard $(SRC)/*.py) \
           $(wildcard $(SRC)/aquarium32/*.py) \
           $(wildcard $(SRC)/uttp/*.py) \
           $(wildcard $(SRC)/uwifimgr/*.py) \
           $(wildcard $(SRC)/pysolar/*.py) \
           $(wildcard $(SRC)/aquarium32/static/*)
OBJ     := ./_put
OBJS    := $(patsubst $(SRC)/%,$(OBJ)/%.done,$(SRCS))

.PHONY: install clean version


$(OBJ)/%.done: $(SRC)/% | $(OBJ)
	ampy --port $(PORT) put $< $< && touch $@

$(OBJ):
	mkdir $@
	mkdir $@/pysolar
	mkdir $@/uwifimgr
	mkdir $@/aquarium32
	mkdir $@/aquarium32/static
	
version:
	git describe --always --tags --dirty > $(OBJ)/aquarium32/version.txt
	ampy --port $(PORT) put $(OBJ)/aquarium32/version.txt aquarium32/version.txt

install: $(OBJS) version

clean:
	rm -r $(OBJ)

shell:
	picocom $(PORT) -b115200

