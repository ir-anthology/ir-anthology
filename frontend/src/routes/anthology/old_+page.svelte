<script lang="ts">
    import { resolve } from '$app/paths';
    let {data} = $props();
    const venues = $derived(data.venues)
    const workshops = $derived(venues.filter(v => v.type === 'Workshop').sort((a, b) => a.label.localeCompare(b.label)))
    const workshop_row = {
        years: [...new Set(workshops.flatMap(v => v.years))],
        label: 'Workshops',
        id: 'workshops',
        type: 'Workshop',
    };
    const conferences = $derived(venues.filter(v => v.type === 'Conference').sort((a, b) => a.label.localeCompare(b.label)))
    conferences.push(workshop_row)
    const journals = $derived(venues.filter(v => v.type === 'Journal').sort((a, b) => a.label.localeCompare(b.label)))
    const allYears = $derived(data.venues.flatMap(v => v.years.map(Number)).filter(y => !isNaN(y)));
    const maxYear = $derived(allYears.length > 0 ? Math.max(...allYears) : new Date().getFullYear());
    const minYear = $derived(allYears.length > 0 ? Math.min(...allYears) : 1960);
    const indicies = $derived(Array.from({ length: maxYear - minYear + 1 }, (_, i) => maxYear - i));
    const decadeGroups = $derived.by(() => {
        const groups: { label: string; span: number }[] = [];
        for (let d = Math.floor(maxYear / 10) * 10; d >= Math.floor(minYear / 10) * 10; d -= 10) {
            const hi = Math.min(d + 9, maxYear);
            const lo = Math.max(d, minYear);
            groups.push({ label: `${hi}–${lo}`, span: hi - lo + 1 });
        }
        return groups;
    });
</script>

{#snippet venueTable(rows: typeof venues)}
<div class="overflow-x-auto">
<table class="min-w-full divide-y divide-gray-200 table-fixed border border-gray-300">
    <colgroup>
        <col style="width: 7rem">
        {#each indicies as index (index)}
            <col style="width: 1.75rem">
        {/each}
    </colgroup>
    <thead class="bg-gray-50 divide-x divide-gray-600">
        <tr class="divide-x divide-gray-300">
            <th class="px-2 py-1 w-20 sticky left-0 z-10 bg-gray-50">Venue</th>
            {#each decadeGroups as group (group.label)}
                <th scope="col" colspan={group.span} class="px-2 py-1">{group.label}</th>
            {/each}
        </tr>
    </thead>
    <tbody>
        {#each rows as venue, i (venue)}
            <tr class={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                <td class="px-4 py-3 text-sm text-gray-900 wrap-break-word w-24 sticky left-0 z-10" class:bg-white={i % 2 === 0} class:bg-gray-50={i % 2 !== 0}>
                    <a href={resolve(`/anthology/venues/${venue.id}`)} class="link font-bold">{venue.label}</a>
                </td>
                {#each indicies as index, j (index)}
                    {@const border = (j === 0 || index % 10 === 9) ? 'border-l border-gray-300' : ''}
                    {#if venue.years.includes(index.toString())}
                        <td class="px-0.5 {border}">
                            <a href={resolve(`/anthology/venues/${venue.id}/${index}`)} class="link">{String(index % 100).padStart(2, '0')}</a>
                        </td>
                    {:else}
                        <td class="px-0.5 {border}"></td>
                    {/if}
                {/each}
            </tr>
        {/each}
    </tbody>
</table>
</div>
{/snippet}

<h1 class="text-2xl mb-4">Venues</h1>

<h2 class="text-xl font-semibold mb-2">Conferences</h2>
{@render venueTable(conferences)}

<h2 class="text-xl font-semibold mt-6 mb-2">Journals</h2>
{@render venueTable(journals)}
