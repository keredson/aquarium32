PORT    := /dev/ttyUSB0
SRC     := .
SRCS    := $(wildcard $(SRC)/*.py) $(wildcard $(SRC)/pysolar/*.py) $(wildcard $(SRC)/static/*)
OBJ     := ./_put
OBJS    := $(patsubst $(SRC)/%,$(OBJ)/%.done,$(SRCS))

.PHONY: install clean


$(OBJ)/%.done: $(SRC)/% | $(OBJ)
	ampy --port $(PORT) put $< $< && touch $@

$(OBJ):
	mkdir $@
	mkdir $@/pysolar
	mkdir $@/static

install: $(OBJS)

clean:
	rm -r $(OBJ)

