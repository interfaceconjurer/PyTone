#!/bin/bash
# chrome.sh in.svg out.png bg [displaywidth]
svg=$(cd "$(dirname "$1")"; pwd)/$(basename "$1"); out=$2; bg=$3; dw=${4:-900}
read w h < <(python3 - "$svg" <<'P'
import re,sys
s=open(sys.argv[1]).read(600); m=re.search(r'width="([\d.]+)" height="([\d.]+)"',s); print(m.group(1),m.group(2))
P
)
H=$(python3 -c "print(int($dw*$h/$w)+2)")
html=/tmp/wrap_$$.html
echo "<html><body style='margin:0;background:$bg'><img src='file://$svg' style='width:${dw}px;display:block'></body></html>" > $html
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --hide-scrollbars --allow-file-access-from-files --force-device-scale-factor=1 --window-size=$dw,$H --screenshot="$out" "file://$html" >/dev/null 2>&1
rm -f $html; echo "$out ${dw}x$H"
