#!/bin/sh
set -e

echo "Generating Static fonts"
mkdir -p ../exports
fontmake -g DMMono-MASTER.glyphs -i -o ttf --output-dir ../exports/
fontmake -g DMMono-Italics-MASTER.glyphs -i -o ttf --output-dir ../exports/

rm -rf master_ufo/ instance_ufo/


echo "Post processing"
ttfs=$(ls ../exports/*.ttf)
for ttf in $ttfs
do
	python -m ttfautohint $ttf $ttf.fix
	mv "$ttf.fix" $ttf;
	gftools fix-hinting $ttf
	mv "$ttf.fix" $ttf;
	gftools fix-isfixedpitch --fonts $ttf;
	mv "$ttf.fix" $ttf;
done

echo "Generating Variable fonts"
vf=../exports/variable
mkdir -p $vf
fontmake -g DMMono-MASTER.glyphs -o variable --output-path $vf/DMMono-VF.ttf
fontmake -g DMMono-Italics-MASTER.glyphs -o variable --output-path $vf/DMMono-Italic-VF.ttf
rm -rf master_ufo/ instance_ufo/
python ../tools/variable.py $vf/DMMono-VF.ttf "$vf/DMMono[wght].ttf"
python ../tools/variable.py $vf/DMMono-Italic-VF.ttf "$vf/DMMono-Italic[wght].ttf" --italic
rm $vf/DMMono-VF.ttf $vf/DMMono-Italic-VF.ttf

echo "Generating Single Line fonts"
python ../tools/singleline/build.py
