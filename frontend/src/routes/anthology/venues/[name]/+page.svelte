<script lang="ts">
    import { resolve } from '$app/paths';
    import { page } from '$app/state';
    import { getIDFromURI } from '$lib/helperFunctions';
    import VenueTypeBadge from '$lib/components/VenueTypeBadge.svelte';

    const { data } = $props();
    const venueName = page.params.name;
</script>
<nav class="text-sm mb-4">
    <a href={resolve('/anthology')} class="link">Main</a> »
</nav>
{#if data.type === 'journal'}
    {@const articles = data.articles ?? new Map()}
    {@const journalTitle = data.journalTitle ?? ''}

    <h1 class="text-3xl font-bold flex items-start gap-3 mb-2">
        <VenueTypeBadge type={data.venueType} />
        <span>{journalTitle}</span>
    </h1>

    <hr class="mb-6">

    <!-- ONE grid for the whole page, not one per year: the label column is sized
         against every row on the page, so the badges line up across year groups too.
         The year cell spans its group's rows (`grid-row: span N`); auto-placement
         then skips the occupied column-1 cells and drops the remaining rows into
         columns 2-4 on its own. `contents` makes each <li>'s children the grid items,
         which keeps the <ul>/<li> list semantics intact. -->
    <ul class="grid grid-cols-[3rem_max-content_max-content_max-content] items-center gap-x-2 gap-y-1">
        {#each articles.keys() as yearKey (yearKey)}
            {@const issues = articles.get(yearKey) ?? []}
            {#each issues as issue, i (`${issue.volume}-${issue.number}`)}
                <li class="contents">
                    {#if i === 0}
                        <a
                            href={resolve(`/anthology/venues/${venueName}/${yearKey}`)}
                            class="link col-start-1 self-start pt-3 text-right font-bold"
                            style="grid-row: span {issues.length}"
                        >{yearKey}</a>
                    {/if}
                    <span class="text-gray-400 {i === 0 ? 'pt-3' : ''}">•</span>
                    <a
                        href={resolve(`/anthology/venues/${venueName}/${yearKey}#v${issue.volume}i${issue.number}`)}
                        class="link {i === 0 ? 'pt-3' : ''}"
                    >
                        {yearKey}{issue.volume != null ? ` Volume ${issue.volume}` : ''}{issue.number != null ? ` Issue ${issue.number}` : ''}
                    </a>
                    <span class="badge-count justify-self-start {i === 0 ? 'mt-3' : ''}">{issue.count} papers</span>
                </li>
            {/each}
        {/each}
    </ul>
{:else}
    {@const yearGroups = data.yearGroups ?? new Map()}

    <h1 class="text-3xl font-bold flex items-start gap-3 mb-2">
        <VenueTypeBadge type={data.venueType} />
        <span>{data.name}</span>
    </h1>

    <hr class="mb-6">

    <!-- PREVIEW (see claude_notes.txt): same page-wide grid as the journal list above.
         Proceedings titles run to ~130 chars, so the title track is capped with
         fit-content(42rem): it shrinks to the longest title when they are short (which
         keeps the badges next to the text) and stops growing after 42rem. Paired with
         `truncate`, every row is a single line ending in an ellipsis, with the full
         title on hover via the title attribute. Tune the 42rem to taste. -->
    <ul class="grid grid-cols-[3rem_max-content_fit-content(42rem)_max-content] gap-x-2 gap-y-1">
        {#each yearGroups.keys() as year (year)}
            {@const proceedings = yearGroups.get(year) ?? []}
            {#each proceedings as proc, i (proc.pub)}
                <li class="contents">
                    {#if i === 0}
                        <a
                            href={resolve(`/anthology/venues/${data.venue_id}/${year}`)}
                            class="link col-start-1 self-start pt-3 text-right font-bold"
                            style="grid-row: span {proceedings.length}"
                        >{year}</a>
                    {/if}
                    <span class="text-gray-400 self-start pt-0.5 {i === 0 ? 'mt-3' : ''}">•</span>
                    {#if proc.title === ''}
                        <a href={resolve(`/anthology/venues/${data.venue_id}/${year}`)} class="link self-start {i === 0 ? 'pt-3' : ''}">Papers without proceedings</a>
                    {:else}
                        <a
                            href={resolve(`/anthology/venues/${data.venue_id}/${year}#${getIDFromURI(proc.pub ?? '')}`)}
                            class="link self-start {i === 0 ? 'pt-3' : ''}"
                            title={proc.title}
                        >{proc.title}</a>
                    {/if}
                    <span class="badge-count justify-self-start self-start {i === 0 ? 'mt-3' : ''}">{proc.count} papers</span>
                </li>
            {/each}
        {/each}
    </ul>
{/if}
