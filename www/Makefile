TARGETS = tupelo-main.js tupelo.js tupelo.css

.PHONY: all clean

all: $(TARGETS)

%.js : %.coffee
	coffee -c $<

%.css : %.less
	lessc $< > $@

clean:
	rm -rf $(TARGETS)
