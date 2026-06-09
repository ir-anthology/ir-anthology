<script lang="ts">
    import { resolve } from '$app/paths';
    import { page } from '$app/state';

    const { data } = $props();
    const venueName = page.params.name;
</script>
<nav class="text-sm mb-4">
    <a href={resolve('/')} class="link">Main</a> »
</nav>
{#if data.type === 'journal'}
    {@const articles = data.articles ?? new Map()}
    {@const journalTitle = data.journalTitle ?? ''}

    <h1 class="text-3xl font-bold mb-2">{journalTitle}</h1>

    <hr class="mb-6">

    {#each articles.keys() as yearKey (yearKey)}
        {@const issues = articles.get(yearKey) ?? []}
        <div class="flex gap-6 mb-4">
            <div class="w-12 text-right font-bold shrink-0 pt-0.5">
                <a href={resolve(`/anthology/venues/${venueName}/${yearKey}`)} class="link">{yearKey}</a>
            </div>
            <ul class="flex-1 space-y-1">
                {#each issues as issue (`${issue.volume}-${issue.number}`)}
                    <li class="flex items-center gap-2">
                        <span class="text-gray-400">•</span>
                        <a href={resolve(`/anthology/venues/${venueName}/${yearKey}#v${issue.volume}i${issue.number}`)} class="link">
                            {yearKey}{issue.volume != null ? ` Volume ${issue.volume}` : ''}{issue.number != null ? ` Issue ${issue.number}` : ''}
                                                </a>
                        <span class="badge-count ml-1">{issue.count} papers</span>
                    </li>
                {/each}
            </ul>
        </div>
    {/each}
{:else}
    {@const yearGroups = data.yearGroups ?? new Map()}

    <h1 class="text-3xl font-bold mb-2">{data.name}</h1>

    <hr class="mb-6">

    {#each yearGroups.keys() as year (year)}
        {@const proceedings = yearGroups.get(year) ?? []}
        <div class="flex gap-6 mb-4">
            <div class="w-12 text-right shrink-0 pt-0.5">
                <a href={resolve(`/anthology/venues/${data.venue_id}/${year}`)} class="link font-bold">{year}</a>
            </div>
            <ul class="flex-1 space-y-1">
                {#each proceedings as proc (proc.pub)}
                    <li class="flex gap-2">
                        <span class="text-gray-400 shrink-0 pt-0.5">•</span>
                        <div>
                            <a href={resolve(`/anthology/venues/${data.venue_id}/${year}`)} class="link">{proc.title}</a>
                            <span class="badge-count ml-1">{proc.count} papers</span>
                        </div>
                    </li>
                {/each}
            </ul>
        </div>
    {/each}
{/if}
