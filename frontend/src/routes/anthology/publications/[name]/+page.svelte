<script lang="ts">
    import { getIDFromURI } from '$lib/helperFunctions';
    import { resolve } from '$app/paths';
    import { createBibTeXString } from '$lib/bibtexHelper.js';
    const {data} = $props()
    const publication = data.publication
    const authors = publication.authors.split(', ')
    const authorIds = publication.authorIds.split(', ')
    console.log(authors)
    console.log(authorIds)
    const bibtexString = createBibTeXString(publication)

    let textareaEl: HTMLTextAreaElement | undefined
    $effect(() => {
        if (textareaEl) {
            textareaEl.style.height = 'auto'
            textareaEl.style.height = textareaEl.scrollHeight + 'px'
        }
    })
</script>

<h1>{publication.title}</h1>
{#each authors as author, i (i)}
    <a href={resolve(`/anthology/people/${getIDFromURI(authorIds[i])}`)}>{author}, </a>
{/each}
<br>
<br>
Volume: {publication.booktitle}
<br>
Year: {publication.year}
<br>
Venue: {publication.streamTitle}
<br>
Publisher: {publication.publisher}
<br>
Pages: {publication.pages}
<br>
URL: {publication.url}
<br>
DOI: {publication.doi}
<br>
DBLP: {publication.pub}
<br>
<br>
<textarea bind:this={textareaEl} readonly style="width: 100%; font-family: monospace; overflow: hidden; resize: none;">{bibtexString}</textarea>
