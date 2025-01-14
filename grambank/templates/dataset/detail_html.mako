<%inherit file="../home_comp.mako"/>
<%namespace name="util" file="../util.mako"/>

<h2>Welcome to GramSunDa</h2>

<p class="lead">
GramSunDa is a database of structural (typological) features of languages of the Lesser Sunda Islands.
It consists of more than 200 logically independent features (most of them binary) spanning all subdomains of morphosyntax.
The GramSunDa feature questionnaire has been expanded from <a href="http://glottobank.org/?grambank">GramBank</a> an been filled in, based on reference grammars and active field work, for about 20 languages and varieties in the region.
</p>

<p>
GramSunDa is produced by a team directed by Marian Klamer, as part of a VICI project at Leiden University Centre for Linguistics.</p>

<p>
The original questionnaire was designed by Ger Reesink and
Michael Dunn, subsequent extensions and clarifications were done by
Hedvig Skirg&aring;rd, Suzanne van der Meer, Harald Hammarstr&ouml;m,
Stephen Levinson, Hannah Haynie, Jeremy Collins, Nicholas Evans, and Hanna Fricke.</p>

<p>
<table class="table table-condensed table-nonfluid">
    <thead>
    <tr>
        <th colspan="3">Statistics</th>
    </tr>
    </thead>
    <tbody>
    <tr><td>Languages</td><td></td><td>${stats['language']}</td></tr>
    <tr><td>Features</td><td></td><td>${stats['parameter']}</td></tr>
    <tr><td>Datapoints</td><td></td><td></td></tr>
    % for name, count in contribs:
        <tr><td></td><td>${name}</td><td>${count}</td></tr>
    % endfor
     <tr><td></td><td><b>total</b></td><td>${stats['value']}</td></tr>
    </tbody>
</table>
</p>


<h3>How to use GramSunDa</h3>
<p>
Using GramSunDa requires a browser with Javascript enabled.
</p>
<p>
You find the features or languages of GramSunDa through the items "Features" and "Languages" in the navigation bar.
</p>


<p>
GramSunDa is a publication of the
<a href="http://www.vici.marianklamer.org/">NWO Vici Grant Research Project (2014-2019) “Reconstructing the past through languages of the present: the Lesser Sunda Islands”</a> at the ${h.external_link('https://www.universiteitleiden.nl/en/humanities/leiden-university-centre-for-linguistics', label='Leiden University Centre for Linguistics')}.
</p>


<h3>How to cite GramSunDa Online</h3>
<p>

</p>

<h3>Terms of use</h3>
<p>
The content of this web site is published.
We invite the community of users to think about further applications for the available data
and look forward to your comments, feedback and questions.
</p>
