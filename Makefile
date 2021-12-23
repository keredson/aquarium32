PORT    := /dev/ttyUSB0
SRC     := .
SRCS    := $(wildcard $(SRC)/*.py) $(wildcard $(SRC)/pysolar/*.py)
OBJ     := ./_put
OBJS    := $(patsubst $(SRC)/%.py,$(OBJ)/%.done,$(SRCS))

.PHONY: install clean


$(OBJ)/%.done: $(SRC)/%.py | $(OBJ)
	ampy --port $(PORT) put $< $< && touch $@

$(OBJ):
	mkdir $@
	mkdir $@/pysolar

install: $(OBJS)

clean:
	rm -r $(OBJ)

