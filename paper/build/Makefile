texengine=pdflatex
zhengine=xelatex
paper := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/..)
root := $(abspath $(paper)/..)
outdir_rel := paper/build/out
outdir := $(root)/$(outdir_rel)
localtex := $(paper)/build/texmf/tex/latex/local//
texfiles := $(root)/main.tex $(wildcard $(paper)/tex/*.tex $(paper)/figure/*.tex)
zhtexfiles := $(root)/main_zh.tex $(paper)/tex/defs_zh.tex $(wildcard $(paper)/tex-zh/*.tex $(paper)/figure-zh/*.tex $(paper)/figure/*.tex)
bibfiles := $(wildcard $(paper)/bib/*.bib)
localtexfiles := $(wildcard $(paper)/build/texmf/tex/latex/local/*)
export TEXINPUTS := $(localtex):$(TEXINPUTS):

$(root)/main.pdf : $(texfiles) $(bibfiles) $(localtexfiles) | $(outdir)
	cd $(root) && ${texengine} --shell-escape -output-directory=$(outdir) main
	cp $(outdir)/main.pdf $(root)/main.pdf

$(root)/main_zh.pdf : $(zhtexfiles) $(bibfiles) $(localtexfiles) | $(outdir)
	cd $(root) && ${zhengine} --shell-escape -interaction=nonstopmode -output-directory=$(outdir) main_zh
	cd $(root) && bibtex $(outdir_rel)/main_zh
	cd $(root) && ${zhengine} --shell-escape -interaction=nonstopmode -output-directory=$(outdir) main_zh
	cd $(root) && ${zhengine} --shell-escape -interaction=nonstopmode -output-directory=$(outdir) main_zh
	cp $(outdir)/main_zh.pdf $(root)/main_zh.pdf

all: $(texfiles) $(bibfiles) $(localtexfiles) | $(outdir)
	cd $(root) && ${texengine} --shell-escape -output-directory=$(outdir) main
	cd $(root) && bibtex $(outdir_rel)/main
	cd $(root) && ${texengine} --shell-escape -output-directory=$(outdir) main
	cd $(root) && ${texengine} --shell-escape -output-directory=$(outdir) main
	cp $(outdir)/main.pdf $(root)/main.pdf

zh: $(root)/main_zh.pdf

full: clean all

$(outdir):
	mkdir -p $(outdir)

clean:
	cd $(root) && ${RM} -rf *.aux *.log *.blg *.ent tmp/* *.auxlock *.bbl *.out *.md5 *.toc *.fls *.fdb_latexmk _minted-main _minted-main_zh
	cd $(root) && ${RM} -rf paper/build/out
	cd $(root) && ${RM} -rf main.pdf main_zh.pdf

pull:
	cd $(root) && git stash
	cd $(root) && git pull --rebase
	cd $(root) && git stash pop
	$(MAKE) -f $(paper)/build/Makefile

push:
	cd $(root) && git commit -am "Pushed using make push"
	cd $(root) && git pull --rebase
	cd $(root) && git push origin main
