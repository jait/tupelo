JSTARGETS = tupelo-main.js tupelo.js

.PHONY: all clean

all: $(JSTARGETS)

%.js : %.coffee
	coffee -c $<

clean:
	rm -rf $(JSTARGETS)
