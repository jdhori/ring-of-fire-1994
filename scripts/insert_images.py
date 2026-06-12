import re, glob, os

ALT = {
 "1-1": "Family-tree diagram tracing five companies back to Raven Arms, founded by George Jennings in 1970. It links Lorcin Engineering, Davis Industries, Phoenix Arms (which took over Raven's tooling after a 1991 fire), Bryco Arms (via Jennings Firearms and Calwestco), and Sundance Industries, each annotated with its founder, founding year, and 1992 production total. The full figures appear in the table below.",
 "2-1": "Line chart comparing total handgun production for each of the six Ring of Fire companies from 1984 to 1992, in thousands of guns. Bryco, Davis, and Lorcin rise steeply after 1989 to roughly 180,000 to 205,000 guns by 1992, while AMT and Sundance remain low.",
 "2-2": "Bar chart of the Ring of Fire companies' share of total U.S. pistol production by caliber in 1992: 36 percent of .22, 83 percent of .25 ACP, 89 percent of .32 ACP, 82 percent of .380 ACP, 0 percent of 9mm, and 2 percent of .45 ACP.",
 "2-3": "Line chart contrasting the combined handgun production of three Gun Valley makers (Smith & Wesson, Ruger, Colt) with the Ring of Fire companies, 1984 to 1992 and projected to 1996. The Gun Valley line falls from about 1,000,000 toward 800,000 while the Ring of Fire line climbs from about 200,000 to meet it, the two crossing around 1995.",
 "2-4": "Bar chart of Relative Stopping Power for ammunition commonly used in Ring of Fire handguns: .22 LR is 5, .25 ACP is 4, .32 ACP is 13, .380 ACP is 27, and 9mm is 58, showing the medium-caliber rounds are far more powerful.",
 "2-5": "Line chart of Ring of Fire handgun production by caliber, 1984 to 1992. The .380 ACP line climbs sharply after 1988 to nearly 300,000 guns by 1992, overtaking .25 ACP and the other small calibers.",
 "2-6": "Line chart of Arcadia Machine & Tool (AMT) handgun production by caliber and in total, 1984 to 1992. Total output peaks near 39,000 guns in 1988, then declines to about 20,000 by 1992.",
 "2-7": "Photograph of the Arcadia Machine & Tool facility in Irwindale, California: a low, light-colored industrial building set behind a paved lot and young trees.",
 "2-8": "Photograph of the AMT Backup pistol, shown actual size. A small stainless semi-automatic pistol with a checkered grip; the slide is marked 'CAL .380 9MM KURZ, BACK UP.'",
 "2-9": "Line chart of Bryco Arms handgun production, including predecessors Jennings Firearms and Calwestco, by caliber and in total, 1984 to 1992. A separate total appears after 1988 and rises steeply to about 205,000 guns by 1992.",
 "2-10": "Photograph of the Bryco Arms facility in Costa Mesa, California: a low industrial building largely screened by mature trees, with an empty parking lot in front.",
 "2-11": "Photograph of the Jennings J-25 pistol made by Bryco Arms, shown actual size. A small black semi-automatic pistol with a ribbed grip.",
 "2-12": "Line chart of Davis Industries handgun production by caliber and in total, 1984 to 1992. Total output climbs steadily to about 185,000 guns by 1992, led by .380 ACP pistols.",
 "2-13": "Photograph of the Davis Industries facility in Mira Loma, California: a modern industrial building with a dark-banded corner entrance, fronted by a landscaped lot.",
 "2-14": "Photograph of a Davis Industries pistol, shown actual size. A small black semi-automatic pistol; the slide is stamped 'DAVIS INDUSTRIES, CHINO, CA, U.S.A.'",
 "2-15": "Line chart of Lorcin Engineering handgun production by caliber and in total, 1984 to 1992. Production begins in 1989 with .25 ACP pistols and rises to roughly 188,000 guns by 1992 as .380 ACP output is added.",
 "2-16": "Photograph of the Lorcin Engineering facility in Mira Loma, California: a long single-story building numbered 10427, with a row of glass storefront windows.",
 "2-17": "Photograph of the Lorcin Engineering L-25 pistol, shown actual size. A small semi-automatic pistol with a bright chrome slide and a dark grip.",
 "2-18": "Line chart of Phoenix Arms handgun production, including predecessor Raven Arms, 1984 to 1992, all in .25 ACP. Output peaks near 160,000 guns in 1989, then falls to about 65,000 by 1992.",
 "2-19": "Photograph of the Phoenix Arms facility in Ontario, California: a modern two-tone industrial building with a glass corner stairwell, fronted by young trees and lawn.",
 "2-20": "Photograph of the Raven P-25 pistol, shown actual size. A small semi-automatic pistol with a chrome finish and dark wood grips.",
 "2-21": "Line chart of Sundance Industries handgun production, 1989 to 1992, all in .25 ACP. Output rises from about 4,000 guns in 1989 to roughly 17,500 in 1992.",
 "2-22": "Photograph of the Sundance Industries facility in Valencia, California: a white single-story commercial unit with signage, behind a striped parking lot.",
 "2-23": "Photograph of the Sundance Industries A-25 pistol, shown actual size. A small semi-automatic pistol with a satin metal slide and a dark grip.",
}

def imgfile(num):
    return "fig-1-1-family-tree.jpg" if num=="1-1" else f"fig-{num}.jpg"

callout_re = re.compile(r'^> \*\*Figure (\d+-\d+)')

count=0
for path in sorted(glob.glob('build/*.md')):
    with open(path) as f: lines=f.readlines()
    out=[]
    for ln in lines:
        m=callout_re.match(ln)
        if m:
            num=m.group(1)
            alt=ALT.get(num, f"Figure {num} from the original report.")
            out.append(f"![{alt}](images/{imgfile(num)})\n")
            out.append("\n")
            count+=1
        out.append(ln)
    with open(path,'w') as f: f.writelines(out)
print(f"Inserted {count} figure images.")
