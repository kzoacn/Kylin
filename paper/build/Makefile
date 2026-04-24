texengine=pdflatex
paper := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/..)
root := $(abspath $(paper)/..)
outdir_rel := paper/build/out
outdir := $(root)/$(outdir_rel)
localtex := $(paper)/build/texmf/tex/latex/local//
texfiles := $(wildcard $(root)/*.tex $(paper)/tex/*.tex $(paper)/figure/*.tex)
bibfiles := $(wildcard $(paper)/bib/*.bib)
localtexfiles := $(wildcard $(paper)/build/texmf/tex/latex/local/*)
export TEXINPUTS := $(localtex):$(TEXINPUTS):

$(root)/main.pdf : $(texfiles) $(bibfiles) $(localtexfiles) | $(outdir)
	cd $(root) && ${texengine} --shell-escape -output-directory=$(outdir) main
	cp $(outdir)/main.pdf $(root)/main.pdf

all: $(texfiles) $(bibfiles) $(localtexfiles) | $(outdir)
	cd $(root) && ${texengine} --shell-escape -output-directory=$(outdir) main
	cd $(root) && bibtex $(outdir_rel)/main
	cd $(root) && ${texengine} --shell-escape -output-directory=$(outdir) main
	cd $(root) && ${texengine} --shell-escape -output-directory=$(outdir) main
	cp $(outdir)/main.pdf $(root)/main.pdf

full: clean all

$(outdir):
	mkdir -p $(outdir)

clean:
	cd $(root) && ${RM} -rf *.aux *.log *.blg *.ent tmp/* *.auxlock *.bbl *.out *.md5
	cd $(root) && ${RM} -rf paper/build/out
	cd $(root) && ${RM} -rf main.pdf

pull:
	cd $(root) && git stash
	cd $(root) && git pull --rebase
	cd $(root) && git stash pop
	$(MAKE) -f $(paper)/build/Makefile

push:
	cd $(root) && git commit -am "Pushed using make push"
	cd $(root) && git pull --rebase
	cd $(root) && git push origin main
