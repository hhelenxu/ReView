from rake_nltk import Rake

# output- not ideal, but 3 word phrases seem to be the best
# orgo: ['relatively uncommon cancer', 'form long chains', 'chronic myelogenous leukemia', 'bcr – abl', 'apply basic skills']
# cs: ['unique application requirements', 'smart home appliances', 'slight modifi cations', 'simple web serving', 'see section 6']
# ece: ['metal conductors results', 'simple circuit consisting', 'area per unit', 'sometimes called nodes', 'sometimes called devices']

# get keywords using Rapid Automatic Keyword Extraction algorithm
def find_keywords(text):
    r = Rake(min_length=1, max_length=3)
    r.extract_keywords_from_text(text)
    return r.get_ranked_phrases()[:5]

orgo = """Organic chemistry is the branch of science that deals generally with compounds of carbon.
There are roughly 15 million known organic compounds. The number of possible organic
compounds is essentially infinite. But all of these have one thing in common: they contain
carbon. The large number of organic compounds results from carbon’s singular ability to
combine with other carbons to form long chains (as you will learn).
B. How Is Organic Chemistry Useful?
This is the structure of the anticancer drug imatinib (marketed as Gleevec®).
Chances are, you might not know how to interpret this structure, but you will learn. Imatinib
illustrates the utility of organic chemistry. Prior to 2001, a medical diagnosis of chronic
myelogenous leukemia (CML), a relatively uncommon cancer of the blood and bone marrow,
was a death sentence. However, an oncologist, Brian Drucker, and a biochemist, Nicholas
Lydon, using results on the genetic basis of CML, were able to screen a number of organic
compounds for their ability to inhibit a key enzyme, bcr–abl. This means that they found a way 
to block the progression of CML. Working with organic chemists, they produced analogs
of their successful compounds (compounds of similar structure), ultimately landing on
imatinib as their drug of choice. Clinical trials, conducted with physician Charles Sawyers,
led to approval of imatinib in 2001 by the Food and Drug Administration (FDA). Imatinib
cured CML in most cases, and it has proven useful in the treatment of other cancers as well.
The ability to rapidly prepare and characterize a large number of organic compounds was
crucial in the development of this drug, and this required a knowledge of organic chemistry.
In the larger picture, the alliance of organic chemistry, molecular biology, and medicine is
clearly the way of the future in the development of effective new drugs, because most drugs
are organic compounds.
By the time you have worked your way through this text, you will certainly understand
the structure and chemical properties of imatinib and many other important molecules.
Should you want to participate in the excitement of drug discovery, you will be prepared for
advanced work that can set you on that road. If you are headed for a career as a practicing
health-care professional, you will be prepared to understand the chemical basis of biochemistry,
which is fundamental to all life sciences.
Organic chemistry is not only useful in medicine. Many useful materials come from
organic chemistry. Things as diverse as textiles, body armor, artificial sweeteners, sports
equipment, and computers are materials, or are based on materials, that come from organic
chemistry.
Apart from its practical utility, organic chemistry is an intellectual discipline that has
both theoretical and experimental aspects. You can use the study of organic chemistry to
develop and apply basic skills in problem solving and, at the same time, to learn a subject of
immense practical value. Whether your goal is to be a professional chemist, to remain in the
mainstream of a health profession, or to be a well-informed citizen in a technological age, you
will find value in the study of organic chemistry.
In this text we have several objectives. We’ll present the “nuts and bolts”—the nomenclature,
classification, structure, and properties of organic compounds. We’ll also cover the
principal reactions and the syntheses of organic molecules. But, more than this, we’ll develop
underlying principles that allow us to understand, and sometimes to predict, reactions rather
than simply memorizing them. We’ll bring some order to the rather daunting array of 15 million
organic molecules, their reactions, and their properties. Along the way, we’ll continue to
highlight some of the important applications of organic chemistry in medicine, industry, and
other areas.
C. The Emergence of Organic Chemistry
Although the applications of organic chemistry, as we have seen, are not restricted to the life
sciences, the name organic certainly implies a connection to living things. In fact, the emergence
of organic chemistry as a science was closely associated with the evolution of the life
sciences.
As early as the sixteenth century, scholars seem to have had some realization that the
phenomenon of life has chemical attributes. Theophrastus Bombastus von Hohenheim, a
Swiss physician and alchemist (ca. 1493–1541) better known as Paracelsus, sought to deal
with medicine in terms of its “elements” mercury, sulfur, and salt. An ailing person was
thought to be deficient in one of these elements and therefore in need of supplementation with
the missing substance. Paracelsus was said to have effected some dramatic “cures” based on
this idea.
By the eighteenth century, chemists were beginning to recognize the chemical aspects
of life processes in a modern sense. Antoine Laurent Lavoisier (1743–1794) recognized the
similarity of respiration to combustion in the uptake of oxygen and expiration of carbon
dioxide."""
print(find_keywords(orgo))

cs = """Classes of Computing Applications and Their
Characteristics
Although a common set of hardware technologies (see Sections 1.4 and 1.5) is used
in computers ranging from smart home appliances to cell phones to the largest
supercomputers, these diff erent applications have diff erent design requirements
and employ the core hardware technologies in diff erent ways. Broadly speaking,
computers are used in three diff erent classes of applications.
Personal computers (PCs) are possibly the best known form of computing,
which readers of this book have likely used extensively. Personal computers
emphasize delivery of good performance to single users at low cost and usually
execute third-party soft ware. Th is class of computing drove the evolution of many
computing technologies, which is only about 35 years old!
Servers are the modern form of what were once much larger computers, and
are usually accessed only via a network. Servers are oriented to carrying large
workloads, which may consist of either single complex applications—usually a
scientifi c or engineering application—or handling many small jobs, such as would
occur in building a large web server. Th ese applications are usually based on
soft ware from another source (such as a database or simulation system), but are
oft en modifi ed or customized for a particular function. Servers are built from the
same basic technology as desktop computers, but provide for greater computing,
storage, and input/output capacity. In general, servers also place a greater emphasis
on dependability, since a crash is usually more costly than it would be on a singleuser
PC.
Servers span the widest range in cost and capability. At the low end, a server
may be little more than a desktop computer without a screen or keyboard and
cost a thousand dollars. Th ese low-end servers are typically used for fi le storage,
small business applications, or simple web serving (see Section 6.10). At the other
extreme are supercomputers, which at the present consist of tens of thousands of
processors and many terabytes of memory, and cost tens to hundreds of millions
of dollars. Supercomputers are usually used for high-end scientifi c and engineering
calculations, such as weather forecasting, oil exploration, protein structure
determination, and other large-scale problems. Although such supercomputers
represent the peak of computing capability, they represent a relatively small fraction
of the servers and a relatively small fraction of the overall computer market in
terms of total revenue.
Embedded computers are the largest class of computers and span the widest
range of applications and performance. Embedded computers include the
microprocessors found in your car, the computers in a television set, and the
networks of processors that control a modern airplane or cargo ship. Embedded
computing systems are designed to run one application or one set of related
applications that are normally integrated with the hardware and delivered as a
single system; thus, despite the large number of embedded computers, most users
never really see that they are using a computer!
Embedded applications oft en have unique application requirements that
combine a minimum performance with stringent limitations on cost or power. For
example, consider a music player: the processor need only be as fast as necessary
to handle its limited function, and beyond that, minimizing cost and power are the
most important objectives. Despite their low cost, embedded computers oft en have
lower tolerance for failure, since the results can vary from upsetting (when your
new television crashes) to devastating (such as might occur when the computer in a
plane or cargo ship crashes). In consumer-oriented embedded applications, such as
a digital home appliance, dependability is achieved primarily through simplicity—
the emphasis is on doing one function as perfectly as possible. In large embedded
systems, techniques of redundancy from the server world are oft en employed.
Although this book focuses on general-purpose computers, most concepts apply
directly, or with slight modifi cations, to embedded computers."""
print(find_keywords(cs))

ece = """The outstanding characteristics of electricity when compared with other power sources are its
mobility and flexibility. Electrical energy can be moved to any point along a couple of wires and,
depending on the user’s requirements, converted to light, heat, or motion.
Consider a simple circuit consisting of two well-known electrical elements, a battery and a
resistor, as shown in Figure 1.2-1. Each element is represented by the two-terminal element
shown in Figure 1.2-2. Elements are sometimes called devices, and terminals are sometimes called
nodes.
Charge may flow in an electric circuit. Current is the time rate of change of charge past a given
point. Charge is the intrinsic property of matter responsible for electric phenomena. The quantity of
charge q can be expressed in terms of the charge on one electron, which is 1.6021019 coulombs.
Thus, 1 coulomb is the charge on 6.241018 electrons. The current through a specified area is
defined by the electric charge passing through the area per unit of time. Thus, q is defined as the charge
expressed in coulombs (C).
Note that throughout this chapter we use a lowercase letter, such as q, to denote a variable that is a
function of time, q(t). We use an uppercase letter, such as Q, to represent a constant.
The flow of current is conventionally represented as a flow of positive charges. This convention
was initiated by Benjamin Franklin, the first great American electrical scientist. Of course, we
now know that charge flow in metal conductors results from electrons with a negative charge.
Nevertheless, we will conceive of current as the flow of positive charge, according to accepted
convention.
Figure 1.2-3 shows the notation that we use to describe a current. There are two parts to
this notation: a value (perhaps represented by a variable name) and an assigned direction. As a
matter of vocabulary, we say that a current exists in or through an element. Figure 1.2-3 shows
that there are two ways to assign the direction of the current through an element. The current i1
is the rate of flow of electric charge from terminal a to terminal b. On the other hand, the
current i2 is the flow of electric charge from terminal b to terminal a. The currents i1 and i2 are
similar but different. They are the same size but have different directions. Therefore, i2 is the negative
of i1 and i1.
We always associate an arrow with a current to denote its direction. A complete description of current
requires both a value (which can be positive or negative) and a direction (indicated by an arrow).
If the current flowing through an element is constant, we represent it by the constant I, as shown in
Figure 1.2-4. A constant current is called a direct current (dc)."""
print(find_keywords(ece))