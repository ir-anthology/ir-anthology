<script lang="ts">
    import { getToken } from '$lib/auth';
    import { importFromDblp, importCustomWorkshop, fetchPatches, type ImportResult } from '$lib/sparql/fetch';

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

    let patches = $state<string[] | null>(null);
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
            customWorkshop.result = await importCustomWorkshop(
                customWorkshop.abbreviation.trim(),
                customWorkshop.title.trim(),
                isNaN(year) ? undefined : year,
                token,
            );
        } catch (e) {
            customWorkshop.error = e instanceof Error ? e.message : 'Unknown error';
        } finally {
            customWorkshop.loading = false;
        }
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
                        class="w-full border border-gray-300 rounded px-3 py-1.5 text-sm focus:outline-none focus:border-gray-500"
                    />
                    <input
                        type="text"
                        placeholder="Abbreviation"
                        bind:value={customWorkshop.abbreviation}
                        required
                        class="w-full border border-gray-300 rounded px-3 py-1.5 text-sm focus:outline-none focus:border-gray-500"
                    />
                    <div class="flex gap-2">
                        <input
                            type="number"
                            placeholder="Year (optional)"
                            bind:value={customWorkshop.year}
                            min="1900"
                            max="2100"
                            class="w-36 border border-gray-300 rounded px-3 py-1.5 text-sm focus:outline-none focus:border-gray-500"
                        />
                        <button
                            type="submit"
                            disabled={customWorkshop.loading}
                            class="px-4 py-1.5 text-sm bg-gray-800 text-white rounded hover:bg-gray-700 disabled:opacity-50 cursor-pointer"
                        >
                            {customWorkshop.loading ? 'Importing…' : 'Import'}
                        </button>
                    </div>
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
                        <ul class="max-h-64 overflow-y-auto flex flex-col gap-1">
                            {#each patches as patch (patch)}
                                <li class="text-sm font-mono bg-gray-50 border border-gray-100 rounded px-2 py-1">{patch}</li>
                            {/each}
                        </ul>
                    {/if}
                {/if}
            </div>

        </div>
    {/if}
</div>
