<script lang="ts">
    import { getIDFromURI, decodeOrdered } from '$lib/helperFunctions';
    import { resolve } from '$app/paths';
    import { createBibtexString } from '$lib/bibtexHelper.js';

    const { data } = $props()
    const publication = data.publication
    const bibtexType = publication.bibtexType?.split("#")[1]
    const authors = decodeOrdered(publication.authors, true)
    const authorIds = decodeOrdered(publication.authorIds)
    const bibtexString = createBibtexString(publication)

    const firstLine = bibtexString.split('\n')[0] ?? ''
    const bibkey = firstLine.slice(firstLine.indexOf('{') + 1).replace(/,$/, '')
    const dblpKey = publication.pub ? publication.pub.replace('https://dblp.org/rec/', '') : ''
    const anthologyId = dblpKey ? `DBLP:${dblpKey}` : ''
    const venueId = publication.stream ? getIDFromURI(publication.stream) : ''
    const venueAbbrev = publication.streamTitle ? publication.streamTitle.split('_')[0].toUpperCase() : ''

    function downloadBibTeX() {
        const blob = new Blob([bibtexString], { type: 'text/plain' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${bibkey}.bib`
        a.click()
        URL.revokeObjectURL(url)
    }

    function copyToClipboard(text: string) {
        navigator.clipboard.writeText(text)
    }

    function selectAll(e: MouseEvent) {
        const range = document.createRange()
        range.selectNodeContents(e.currentTarget as HTMLElement)
        const sel = window.getSelection()
        sel?.removeAllRanges()
        sel?.addRange(range)
    }
</script>

<nav class="text-sm mb-4">
    <a href={resolve('/')}>Main</a> »
    {#if venueId}
        <a href={resolve(`/anthology/venues/${venueId}`)} class="link">{venueAbbrev}</a> »
        <a href={resolve(`/anthology/venues/${venueId}/${publication.year}`)} class="link">{publication.year}</a> »

    {/if}
</nav>

<h1 class="text-3xl font-bold mb-2">{publication.title}</h1>

<p class="mb-4">
    {#each authors as author, i (i)}
        <a href={resolve(`/anthology/people/${getIDFromURI(authorIds[i])}`)} class="link">{author}</a>{#if i < authors.length - 1}<span class="text-gray-400 font-bold px-1.5">|</span>{/if}
    {/each}
</p>

<hr class="mb-4">

<table class="mb-6">
    <tbody>
        {#if anthologyId}
        <tr>
            <th class="text-right font-bold pr-4 py-0.5 whitespace-nowrap">Anthology ID:</th>
            <td class="py-0.5">{anthologyId}</td>
        </tr>
        {/if}
        {#if publication.booktitle}
        <tr>
            <th class="text-right font-bold pr-4 py-0.5 whitespace-nowrap">Volume:</th>
            <td class="py-0.5">
                {#if venueId}
                    <a href={resolve(`/anthology/venues/${venueId}/${publication.year}`)} class="link">{publication.booktitle}</a>
                {:else}
                    {publication.booktitle}
                {/if}
            </td>
        </tr>
        {/if}
        <tr>
            <th class="text-right font-bold pr-4 py-0.5 whitespace-nowrap">Year:</th>
            <td class="py-0.5">{publication.year}</td>
        </tr>
        {#if publication.streamTitle}
        <tr>
            <th class="text-right font-bold pr-4 py-0.5 whitespace-nowrap">Venue:</th>
            <td class="py-0.5">
                {#if venueId}
                    <a href={resolve(`/anthology/venues/${venueId}`)} class="link">{publication.streamTitle}</a>
                {:else}
                    {publication.streamTitle}
                {/if}
            </td>
        </tr>
        {/if}
        {#if publication.publisher}
        <tr>
            <th class="text-right font-bold pr-4 py-0.5 whitespace-nowrap">Publisher:</th>
            <td class="py-0.5">{publication.publisher}</td>
        </tr>
        {/if}
        {#if publication.pages}
        <tr>
            <th class="text-right font-bold pr-4 py-0.5 whitespace-nowrap">Pages:</th>
            <td class="py-0.5">{publication.pages}</td>
        </tr>
        {/if}
        {#if publication.url}
        <tr>
            <th class="text-right font-bold pr-4 py-0.5 whitespace-nowrap">URL:</th>
            <td class="py-0.5"><a href={publication.url} class="link">{publication.url}</a></td>
        </tr>
        {/if}
        {#if publication.doi}
        <tr>
            <th class="text-right font-bold pr-4 py-0.5 whitespace-nowrap">DOI:</th>
            <td class="py-0.5"><a href={`https://doi.org/${publication.doi}`} class="link">{publication.doi}</a></td>
        </tr>
        {/if}
        {#if dblpKey}
        <tr>
            <th class="text-right font-bold pr-4 py-0.5 whitespace-nowrap">DBLP:</th>
            <td class="py-0.5"><a href={publication.pub} class="link">{dblpKey}</a></td>
        </tr>
        {/if}
        <tr>
            <th class="text-right font-bold pr-4 py-0.5 align-top whitespace-nowrap">BibTeX:</th>
            <td class="py-0.5 flex gap-2 flex-wrap">
                <button onclick={downloadBibTeX} class="btn-outline">Download</button>
                <button onclick={() => copyToClipboard(bibtexString)} class="btn-outline">📋 Copy BibTeX to Clipboard</button>
                <button onclick={() => copyToClipboard(bibkey)} class="btn-outline">📋 Copy Bibkey "{bibkey}" to Clipboard</button>
            </td>
        </tr>
    </tbody>
</table>

<div
    role="textbox"
    aria-readonly="true"
    aria-multiline="true"
    tabindex="0"
    onclick={selectAll}
    onkeydown={(e) => e.key === 'Enter' && selectAll(e as unknown as MouseEvent)}
    class="bg-gray-50 border border-gray-200 p-4 text-sm font-mono overflow-x-auto cursor-pointer whitespace-pre"
>{bibtexString}</div>
