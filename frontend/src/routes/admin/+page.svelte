<script lang="ts">
    import { getToken } from '$lib/auth';
    import { importFromDblp, importCustomWorkshop, previewCustomWorkshop, fetchPatches, type ImportResult, type WorkshopProceeding, type PatchRecord } from '$lib/sparql/fetch';

    const { data } = $props();
    const profile = $derived(data.user.profile);
    const groups = $derived(profile['groups_direct'] as string[] | undefined);
    const isAdmin = $derived(groups?.includes('auth/auth-webis-admin') ?? false);
    const name = $derived(profile.name ?? profile.nickname ?? profile.sub);

    type FormState = {
        iri: string;
        year: string;
        loading: boolean;
        result: ImportResult | null;
        error: string | null;
    };

    type CustomWorkshopState = {
        abbreviation: string;
        title: string;
        year: string;
        loading: boolean;
        result: ImportResult | null;
        error: string | null;
        step: 'form' | 'select' | 'done';
        proceedings: WorkshopProceeding[];
        selectedProcs: Set<string>;
    };

    function makeForm(): FormState {
        return { iri: '', year: '', loading: false, result: null, error: null };
    }

    const journal     = $state(makeForm());
    const conference  = $state(makeForm());
    const workshop    = $state(makeForm());
    const person      = $state(makeForm());
    const publication = $state(makeForm());
    const customWorkshop = $state<CustomWorkshopState>({
        abbreviation: '', title: '', year: '', loading: false, result: null, error: null,
        step: 'form', proceedings: [], selectedProcs: new Set(),
    });

    async function submit(form: FormState, type: string) {
        form.result = null;
        form.error = null;
        form.loading = true;
        try {
            const token = await getToken();
            const year = parseInt(form.year);
            form.result = await importFromDblp(form.iri.trim(), type, isNaN(year) ? undefined : year, token);
        } catch (e) {
            form.error = e instanceof Error ? e.message : 'Unknown error';
        } finally {
            form.loading = false;
        }
    }

    let patches = $state<PatchRecord[] | null>(null);
    let patchesLoading = $state(false);
    let patchesError = $state<string | null>(null);

    async function loadPatches() {
        patchesLoading = true;
        patchesError = null;
        try {
            const token = await getToken();
            patches = await fetchPatches(token);
        } catch (e) {
            patchesError = e instanceof Error ? e.message : 'Unknown error';
        } finally {
            patchesLoading = false;
        }
    }

    async function submitCustomWorkshop() {
        customWorkshop.result = null;
        customWorkshop.error = null;
        customWorkshop.loading = true;
        try {
            const token = await getToken();
            const year = parseInt(customWorkshop.year);
            const { proceedings } = await previewCustomWorkshop(
                customWorkshop.abbreviation.trim(),
                customWorkshop.title.trim(),
                isNaN(year) ? undefined : year,
                token,
            );
            if (proceedings.length === 0) {
                customWorkshop.error = 'No proceedings found on DBLP matching the given name/abbreviation';
                return;
            }
            customWorkshop.proceedings = proceedings;
            customWorkshop.selectedProcs = new Set(proceedings.map(p => p.proc));
            customWorkshop.step = 'select';
        } catch (e) {
            customWorkshop.error = e instanceof Error ? e.message : 'Unknown error';
        } finally {
            customWorkshop.loading = false;
        }
    }

    async function confirmCustomWorkshop() {
        customWorkshop.result = null;
        customWorkshop.error = null;
        customWorkshop.loading = true;
        try {
            const token = await getToken();
            const year = parseInt(customWorkshop.year);
            customWorkshop.result = await importCustomWorkshop(
                customWorkshop.abbreviation.trim(),
                customWorkshop.title.trim(),
                isNaN(year) ? undefined : year,
                [...customWorkshop.selectedProcs],
                token,
            );
            customWorkshop.step = 'form';
            customWorkshop.proceedings = [];
            customWorkshop.selectedProcs = new Set();
        } catch (e) {
            customWorkshop.error = e instanceof Error ? e.message : 'Unknown error';
        } finally {
            customWorkshop.loading = false;
        }
    }

    function resetCustomWorkshop() {
        customWorkshop.step = 'form';
        customWorkshop.proceedings = [];
        customWorkshop.selectedProcs = new Set();
        customWorkshop.result = null;
        customWorkshop.error = null;
    }
</script>

<div class="max-w-2xl mx-auto">
    <div class="flex items-center gap-4 mb-8">
        {#if profile.picture}
            <img src={profile.picture} alt="avatar" class="w-14 h-14 rounded-full border border-gray-200">
        {/if}
        <div>
            <h1 class="text-2xl font-semibold">Welcome, {name}.</h1>
                {#if isAdmin}
                    <span class="text-xs font-medium bg-red-100 text-red-700 border border-red-200 rounded px-2 py-0.5">Admin</span>
                {/if}
        </div>
    </div>

    {#if !isAdmin}
        <p class="text-gray-500 text-sm">You don't have admin permissions.</p>
    {:else}
        <div class="flex flex-col gap-6">

            {#snippet importForm(label: string, form: FormState, type: string, withYear: boolean)}
                <div class="border border-gray-200 rounded-lg p-4">
                    <h2 class="text-base font-semibold mb-3">Add {label}</h2>
                    <form onsubmit={(e) => { e.preventDefault(); submit(form, type); }} class="flex flex-col gap-2">
                        <div class="flex gap-2">
                            <input
                                type="url"
                                placeholder="{label} IRI (e.g. https://dblp.org/…)"
                                bind:value={form.iri}
                                required
                                class="flex-1 border border-gray-300 rounded px-3 py-1.5 text-sm focus:outline-none focus:border-gray-500"
                            />
                            {#if withYear}
                                <input
                                    type="number"
                                    placeholder="Year (optional)"
                                    bind:value={form.year}
                                    min="1900"
                                    max="2100"
                                    class="w-36 border border-gray-300 rounded px-3 py-1.5 text-sm focus:outline-none focus:border-gray-500"
                                />
                            {/if}
                            <button
                                type="submit"
                                disabled={form.loading}
                                class="px-4 py-1.5 text-sm bg-gray-800 text-white rounded hover:bg-gray-700 disabled:opacity-50 cursor-pointer"
                            >
                                {form.loading ? 'Importing…' : 'Import'}
                            </button>
                        </div>
                        {#if form.result}
                            <p class="text-sm text-green-700">
                                Added {form.result.triples} triple{form.result.triples === 1 ? '' : 's'}
                                — saved as <code class="font-mono">{form.result.filename}</code>
                                {form.result.live_applied ? '· applied live' : '· live update failed, patch saved'}
                            </p>
                        {/if}
                        {#if form.error}
                            <p class="text-sm text-red-600">{form.error}</p>
                        {/if}
                    </form>
                </div>
            {/snippet}

            {@render importForm('Journal',     journal,     'journal',     true)}
            {@render importForm('Conference',  conference,  'conference',  true)}
            {@render importForm('Workshop',    workshop,    'workshop',    true)}
            {@render importForm('Person',      person,      'person',      false)}
            {@render importForm('Publication', publication, 'publication', false)}

            <div class="border border-gray-200 rounded-lg p-4">
                <h2 class="text-base font-semibold mb-1">Add Unlisted Workshop</h2>
                <p class="text-xs text-gray-500 mb-3">Searches DBLP proceedings by title/abbreviation and groups matching papers under a custom workshop stream.</p>
                <form onsubmit={(e) => { e.preventDefault(); submitCustomWorkshop(); }} class="flex flex-col gap-2">
                    <input
                        type="text"
                        placeholder="Full title"
                        bind:value={customWorkshop.title}
                        required
                        disabled={customWorkshop.step !== 'form'}
                        class="w-full border border-gray-300 rounded px-3 py-1.5 text-sm focus:outline-none focus:border-gray-500 disabled:bg-gray-50 disabled:text-gray-400"
                    />
                    <input
                        type="text"
                        placeholder="Abbreviation"
                        bind:value={customWorkshop.abbreviation}
                        required
                        disabled={customWorkshop.step !== 'form'}
                        class="w-full border border-gray-300 rounded px-3 py-1.5 text-sm focus:outline-none focus:border-gray-500 disabled:bg-gray-50 disabled:text-gray-400"
                    />
                    <div class="flex gap-2">
                        <input
                            type="number"
                            placeholder="Year (optional)"
                            bind:value={customWorkshop.year}
                            min="1900"
                            max="2100"
                            disabled={customWorkshop.step !== 'form'}
                            class="w-36 border border-gray-300 rounded px-3 py-1.5 text-sm focus:outline-none focus:border-gray-500 disabled:bg-gray-50 disabled:text-gray-400"
                        />
                        {#if customWorkshop.step === 'form'}
                            <button
                                type="submit"
                                disabled={customWorkshop.loading}
                                class="px-4 py-1.5 text-sm bg-gray-800 text-white rounded hover:bg-gray-700 disabled:opacity-50 cursor-pointer"
                            >
                                {customWorkshop.loading ? 'Searching…' : 'Search'}
                            </button>
                        {/if}
                    </div>

                    {#if customWorkshop.step === 'select'}
                        <div class="mt-1 flex flex-col gap-1">
                            <p class="text-xs text-gray-500">Select the proceedings to include:</p>
                            <ul class="flex flex-col gap-1">
                                {#each customWorkshop.proceedings as p (p.proc)}
                                    <li>
                                        <label class="flex items-center gap-2 text-sm cursor-pointer">
                                            <input
                                                type="checkbox"
                                                checked={customWorkshop.selectedProcs.has(p.proc)}
                                                onchange={(e) => {
                                                    if (e.currentTarget.checked) customWorkshop.selectedProcs.add(p.proc);
                                                    else customWorkshop.selectedProcs.delete(p.proc);
                                                }}
                                            />
                                            <a href={p.proc} target="_blank" rel="noopener noreferrer" class="link">{p.title}</a> ({p.year})
                                        </label>
                                    </li>
                                {/each}
                            </ul>
                            <div class="flex gap-2 mt-1">
                                <button
                                    type="button"
                                    onclick={confirmCustomWorkshop}
                                    disabled={customWorkshop.loading || customWorkshop.selectedProcs.size === 0}
                                    class="px-4 py-1.5 text-sm bg-gray-800 text-white rounded hover:bg-gray-700 disabled:opacity-50 cursor-pointer"
                                >
                                    {customWorkshop.loading ? 'Importing…' : 'Confirm'}
                                </button>
                                <button
                                    type="button"
                                    onclick={resetCustomWorkshop}
                                    class="px-4 py-1.5 text-sm border border-gray-300 rounded hover:bg-gray-50 cursor-pointer text-sm"
                                >
                                    Cancel
                                </button>
                            </div>
                        </div>
                    {/if}

                    {#if customWorkshop.result}
                        <p class="text-sm text-green-700">
                            Added {customWorkshop.result.triples} triple{customWorkshop.result.triples === 1 ? '' : 's'}
                            — saved as <code class="font-mono">{customWorkshop.result.filename}</code>
                            {customWorkshop.result.live_applied ? '· applied live' : '· live update failed, patch saved'}
                        </p>
                    {/if}
                    {#if customWorkshop.error}
                        <p class="text-sm text-red-600">{customWorkshop.error}</p>
                    {/if}
                </form>
            </div>

            <div class="border border-gray-200 rounded-lg p-4">
                <div class="flex items-center justify-between mb-3">
                    <h2 class="text-base font-semibold">Patches</h2>
                    <button
                        onclick={loadPatches}
                        disabled={patchesLoading}
                        class="px-4 py-1.5 text-sm bg-gray-800 text-white rounded hover:bg-gray-700 disabled:opacity-50 cursor-pointer"
                    >
                        {patchesLoading ? 'Loading…' : 'Show Patches'}
                    </button>
                </div>
                {#if patchesError}
                    <p class="text-sm text-red-600">{patchesError}</p>
                {:else if patches !== null}
                    {#if patches.length === 0}
                        <p class="text-sm text-gray-500">No patches found.</p>
                    {:else}
                        <div class="max-h-96 overflow-y-auto">
                            <table class="w-full text-xs border-collapse">
                                <thead class="sticky top-0 bg-gray-50">
                                    <tr class="text-left text-gray-500 border-b border-gray-200">
                                        <th class="py-1.5 pr-3 font-medium">Time</th>
                                        <th class="py-1.5 pr-3 font-medium">User</th>
                                        <th class="py-1.5 pr-3 font-medium">Action</th>
                                        <th class="py-1.5 pr-3 font-medium">Details</th>
                                        <th class="py-1.5 pr-3 font-medium text-right">Triples</th>
                                        <th class="py-1.5 font-medium">Live</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {#each patches as p (p.filename)}
                                        {@const det = p.details}
                                        <tr class="border-b border-gray-100 align-top">
                                            <td class="py-1.5 pr-3 whitespace-nowrap text-gray-500 font-mono">
                                                {p.timestamp ? p.timestamp.replace('T', ' ').replace('+00:00', 'Z').slice(0, 19) + 'Z' : p.filename.slice(0, 19)}
                                            </td>
                                            <td class="py-1.5 pr-3 whitespace-nowrap">{p.user_name ?? '—'}</td>
                                            <td class="py-1.5 pr-3 whitespace-nowrap">{p.action ?? '—'}</td>
                                            <td class="py-1.5 pr-3 text-gray-700">
                                                {#if det}
                                                    {#if p.action === 'import'}
                                                        <span class="font-medium">{String(det.type)}</span>
                                                        {#if det.iri}<a href={String(det.iri)} target="_blank" rel="noopener noreferrer" class="link ml-1 break-all">{String(det.iri).split('/').at(-1)}</a>{/if}
                                                        {#if det.year}<span class="text-gray-400 ml-1">({det.year})</span>{/if}
                                                    {:else if p.action === 'custom_workshop'}
                                                        <span class="font-medium">{String(det.abbreviation ?? '')}</span>
                                                        {#if det.title}<span class="text-gray-500 ml-1">{String(det.title)}</span>{/if}
                                                        {#if det.year}<span class="text-gray-400 ml-1">({det.year})</span>{/if}
                                                    {:else}
                                                        {JSON.stringify(det)}
                                                    {/if}
                                                {:else}
                                                    <span class="font-mono text-gray-400">{p.filename}</span>
                                                {/if}
                                            </td>
                                            <td class="py-1.5 pr-3 text-right">{p.triples ?? '—'}</td>
                                            <td class="py-1.5">
                                                {#if p.live_applied === true}
                                                    <span class="text-green-600">✓</span>
                                                {:else if p.live_applied === false}
                                                    <span class="text-red-500">✗</span>
                                                {:else}
                                                    <span class="text-gray-400">—</span>
                                                {/if}
                                            </td>
                                        </tr>
                                    {/each}
                                </tbody>
                            </table>
                        </div>
                    {/if}
                {/if}
            </div>

        </div>
    {/if}
</div>
