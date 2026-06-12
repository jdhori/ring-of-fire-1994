import re, glob
img_re = re.compile(r'^!\[.*\]\((images/[^)]+)\)\s*$')
total_removed=0
for path in sorted(glob.glob('build/*.md')):
    with open(path) as f: lines=f.readlines()
    # find target of each image line
    def target(i):
        m=img_re.match(lines[i]); return m.group(1) if m else None
    keep=[True]*len(lines)
    i=0
    while i < len(lines):
        t=target(i)
        if t:
            # look ahead: skip blanks, if next content line is an image with same target, drop THIS one
            j=i+1
            while j<len(lines) and lines[j].strip()=='':
                j+=1
            if j<len(lines) and target(j)==t:
                # drop current image line and following blanks up to j
                for k in range(i,j):
                    keep[k]=False
                total_removed+=1
                i=j
                continue
        i+=1
    newlines=[l for l,k in zip(lines,keep) if k]
    with open(path,'w') as f: f.writelines(newlines)
print(f"Removed {total_removed} duplicate image blocks.")
