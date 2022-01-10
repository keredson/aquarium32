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

.PHONY: install clean


$(OBJ)/%.done: $(SRC)/% | $(OBJ)
	ampy --port $(PORT) put $< $< && touch $@

$(OBJ):
	mkdir $@
	mkdir $@/pysolar
	mkdir $@/uwifimgr
	mkdir $@/aquarium32
	mkdir $@/aquarium32/static

install: $(OBJS)

clean:
	rm -r $(OBJ)

shell:
	picocom $(PORT) -b115200

