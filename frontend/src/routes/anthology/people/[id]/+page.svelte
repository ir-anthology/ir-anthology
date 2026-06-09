<script lang="ts">
    import { resolve } from '$app/paths';
    import { getIDFromURI } from '$lib/helperFunctions';

    const { data } = $props()
    const pubsByYear = $derived(data.pubsByYear ?? new Map())

    const nameParts = $derived((data.name ?? '').split(' '))
    const firstName = $derived(nameParts.slice(0, -1).join(' '))
    const lastName = $derived(nameParts.at(-1) ?? '')

    function splitList(s: string | null): string[] {
        return s ? s.split(', ') : []
    }
</script>

<h1 class="text-3xl mb-2">{firstName} <strong>{lastName}</strong></h1>

<hr class="mb-6">

{#each pubsByYear.keys() as year (year)}
    <h2 class="text-2xl font-bold mb-3">{year}</h2>

    {#each pubsByYear.get(year) ?? [] as pub (pub.pub)}
        {@const authors = splitList(pub.authors)}
        {@const authorIds = splitList(pub.authorIds)}
        <div class="flex gap-3 mb-5 items-start">
            <div class="flex gap-1 shrink-0 mt-0.5">
                {#if pub.doi}
                    <a href="https://doi.org/{pub.doi}" class="badge-doi">doi</a>
                {/if}
                <a href={pub.pub ?? '#'} class="badge-dblp">dblp</a>
            </div>
            <div>
                <a href={resolve(`/anthology/publications/${getIDFromURI(pub.pub ?? '')}`)} class="link-title">
                    {pub.title}
                </a>
                {#if authors.length > 0}
                    <div class="text-sm mt-0.5">
                        {#each authors as author, i (i)}
                            {#if i > 0}<span class="text-gray-400 font-bold px-1.5">|</span>{/if}{#if authorIds[i]}<a href={resolve(`/anthology/people/${getIDFromURI(authorIds[i])}`)} class="link">{author}</a>{:else}{author}{/if}
                        {/each}
                    </div>
                {/if}
                {#if pub.booktitle}
                    <div class="text-sm text-gray-500 mt-0.5">
                        <a href={resolve(`/anthology/venues/${getIDFromURI(pub.stream ?? '')}/${year}`)} class="hover:underline">{pub.booktitle}</a>
                    </div>
                {/if}
            </div>
        </div>
    {/each}
{/each}
