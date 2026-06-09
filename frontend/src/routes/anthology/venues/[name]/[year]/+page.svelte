<script lang="ts">
    import { resolve } from '$app/paths';
    import { page } from '$app/state';
    import { getIDFromURI, decodeOrdered } from '$lib/helperFunctions';

    const { data } = $props()
    const urlParts = page.url.pathname.split('/')
    const year = urlParts.at(-1)!
    const venueName = urlParts.at(-2)!
</script>

{#if Object.keys(data).includes("articles")}
    {@const articles = data.articles ?? new Map()}
    {@const journalTitle = data.journalTitle ?? ''}
    {@const venueAbbrev = journalTitle.split('_')[0].toUpperCase()}

    <nav class="text-sm mb-4">
        <a href={resolve('/')} class="link">Main</a> »
        <a href={resolve(`/anthology/venues/${venueName}`)} class="link">{venueAbbrev}</a> »
    </nav>

    <h1 class="text-3xl font-bold mb-4">{journalTitle} ({year})</h1>

    <hr class="mb-6">

    <div class="border border-gray-200 rounded-lg p-4 mb-8">
        <h2 class="text-base font-semibold mb-2">Content</h2>
        <ul class="space-y-1">
            {#each articles.keys() as vol (vol)}
                {#each (articles.get(vol) ?? new Map()).keys() as iss (iss)}
                    {@const count = (articles.get(vol)?.get(iss) ?? []).length}
                    <li class="flex items-center gap-2">
                        <span class="text-gray-400">•</span>
                        <a href="#v{vol}i{iss}" class="link">
                            {year} Volume {vol} Issue {iss}
                        </a>
                        <span class="badge-count">{count} {count === 1 ? 'paper' : 'papers'}</span>
                    </li>
                {/each}
            {/each}
        </ul>
    </div>

    {#each articles.keys() as vol (vol)}
        {#each (articles.get(vol) ?? new Map()).keys() as iss (iss)}
            {@const entries = articles.get(vol)?.get(iss) ?? []}

            <p class="mb-2"><a href="#" class="text-sm text-gray-500 hover:underline">↑ up</a></p>

            <h2 id="v{vol}i{iss}" class="text-2xl font-bold">
                {year} Volume {vol} Issue {iss}
            </h2>
            <hr class="border-gray-300 mb-4">

            {#each entries as entry (entry.pub)}
                {@const authors = decodeOrdered(entry.authors, true)}
                {@const authorIds = decodeOrdered(entry.authorIds)}
                <div class="flex gap-3 mb-4 items-start">
                    <div class="flex gap-1 shrink-0 mt-0.5">
                        {#if entry.doi}
                            <a href="https://doi.org/{entry.doi}" class="badge-doi">doi</a>
                        {/if}
                        <a href={entry.pub ?? '#'} class="badge-dblp">dblp</a>
                    </div>
                    <div>
                        <a href={resolve(`/anthology/publications/${getIDFromURI(entry.pub ?? '')}`)} class="link font-semibold">
                            {entry.title}
                        </a>
                        {#if authors.length > 0}
                            <div class="text-sm mt-0.5">
                                {#each authors as author, i (i)}
                                    {#if i > 0}<span class="text-gray-400 px-1.5"> | </span>{/if}{#if authorIds[i]}<a href={resolve(`/anthology/people/${getIDFromURI(authorIds[i])}`)} class="link">{author}</a>{:else}{author}{/if}
                                {/each}
                            </div>
                        {/if}
                    </div>
                </div>
            {/each}
        {/each}
    {/each}
{:else}
    {@const proceedings = data.proceedings}
    {@const streamTitle = proceedings?.[0]?.streamTitle ?? ''}
    {@const venueAbbrev = streamTitle.split('_')[0].toUpperCase()}

    <nav class="text-sm mb-4">
        <a href={resolve('/')} class="link">Main</a> »
        <a href={resolve(`/anthology/venues/${venueName}`)} class="link">{venueAbbrev}</a> »
    </nav>

    <h1 class="text-3xl font-bold mb-2">{streamTitle} ({year})</h1>

    <hr class="mb-4">

    <p class="mb-6"><a href={resolve(`/anthology/venues/${venueName}`)} class="text-sm hover:underline">↑ up</a></p>

    {#each proceedings as proceeding (proceeding.pub)}
        {@const procId = getIDFromURI(proceeding.pub ?? '')}
        <p class="mb-4">
            <a href={resolve(`/anthology/publications/${procId}`)} class="link text-2xl leading-snug">
                {proceeding.title}
            </a>
        </p>

        <div class="flex gap-3 mb-4 items-start">
            <div class="flex gap-1 shrink-0 mt-0.5">
                {#if proceeding.doi}
                    <a href="https://doi.org/{proceeding.doi}" class="badge-doi">doi</a>
                {/if}
                <a href={proceeding.pub ?? '#'} class="badge-dblp">dblp</a>
            </div>
            <div>
                <a href={resolve(`/anthology/publications/${procId}`)} class="link-title">
                    {proceeding.title}
                </a>
            </div>
        </div>

        {#each data.inproceedings[proceeding.pub ?? ''] ?? [] as paper (paper.pub)}
            {@const authors = decodeOrdered(paper.authors, true)}
            {@const authorIds = decodeOrdered(paper.authorIds)}
            <div class="flex gap-3 mb-4 items-start">
                <div class="flex gap-1 shrink-0 mt-0.5">
                    {#if paper.doi}
                        <a href="https://doi.org/{paper.doi}" class="badge-doi">doi</a>
                    {/if}
                    <a href={paper.pub} class="badge-dblp">dblp</a>
                </div>
                <div>
                    <a href={resolve(`/anthology/publications/${paper.id}`)} class="link-title">
                        {paper.title}
                    </a>
                    {#if authors.length > 0}
                        <div class="text-sm mt-0.5">
                            {#each authors as author, i (i)}
                                {#if i > 0}<span class="text-gray-400 px-1.5"> | </span>{/if}{#if authorIds[i]}<a href={resolve(`/anthology/people/${getIDFromURI(authorIds[i])}`)} class="link">{author}</a>{:else}{author}{/if}
                            {/each}
                        </div>
                    {/if}
                </div>
            </div>
        {/each}
    {/each}
{/if}
