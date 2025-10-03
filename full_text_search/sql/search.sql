CREATE TYPE search_result AS (
    id INTEGER,
    title TEXT,
    subtitle TEXT,
    author_name TEXT,
    published_at TIMESTAMP WITH TIME ZONE,
    rank FLOAT4,
    highlight TEXT
);


CREATE OR REPLACE FUNCTION search_articles(
    search_query TEXT,
    category_filter INTEGER[] DEFAULT NULL,
    tag_filter TEXT[] DEFAULT NULL,
    author_filter INTEGER[] DEFAULT NULL,
    min_date TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    max_date TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    page_size INTEGER DEFAULT 20,
    page_number INTEGER DEFAULT 1
) RETURNS TABLE (
    results search_result,
    total_count BIGINT
) AS $$
-- DECLARE
--     tsquery_var tsquery;
--     total BIGINT;
-- BEGIN
--     -- Convert search query to tsquery, handling multiple words
--     SELECT array_to_string(array_agg(lexeme || ':*'), ' & ')
--     FROM unnest(regexp_split_to_array(trim(search_query), '\s+')) lexeme
--     INTO search_query;
    
--     tsquery_var := to_tsquery('english', search_query);
DECLARE
    tsquery_var tsquery;
    total BIGINT;
    ts_query_text TEXT;
BEGIN
    -- Convert search query to tsquery format
    SELECT array_to_string(array_agg(lexeme || ':*'), ' & ')
    INTO ts_query_text
    FROM unnest(regexp_split_to_array(trim(search_query), '\s+')) lexeme;

    tsquery_var := to_tsquery('english', ts_query_text);

    -- Get total count for pagination
    SELECT COUNT(DISTINCT a.id)
    FROM articles a
    LEFT JOIN article_categories ac ON a.id = ac.article_id
    LEFT JOIN article_tags at ON a.id = at.article_id
    LEFT JOIN tags t ON at.tag_id = t.id
    WHERE a.status = 'published'
    AND a.search_vector @@ tsquery_var
    AND (category_filter IS NULL OR ac.category_id = ANY(category_filter))
    AND (tag_filter IS NULL OR t.name = ANY(tag_filter))
    AND (author_filter IS NULL OR a.author_id = ANY(author_filter))
    AND (min_date IS NULL OR a.published_at >= min_date)
    AND (max_date IS NULL OR a.published_at <= max_date)
    INTO total;

    RETURN QUERY
    WITH ranked_articles AS (
        SELECT DISTINCT ON (a.id)
            a.id,
            a.title,
            a.subtitle,
            auth.name as author_name,
            a.published_at,
            ts_rank(a.search_vector, tsquery_var) * 
            CASE 
                WHEN a.published_at > NOW() - INTERVAL '7 days' THEN 1.5  -- Boost recent articles
                WHEN a.published_at > NOW() - INTERVAL '30 days' THEN 1.2
                ELSE 1.0
            END as rank,
            ts_headline('english', a.content, tsquery_var, 'StartSel=<mark>, StopSel=</mark>, MaxFragments=1, MaxWords=50, MinWords=20') as highlight
        FROM articles a
        JOIN authors auth ON a.author_id = auth.id
        LEFT JOIN article_categories ac ON a.id = ac.article_id
        LEFT JOIN article_tags at ON a.id = at.article_id
        LEFT JOIN tags t ON at.tag_id = t.id
        WHERE a.status = 'published'
        AND a.search_vector @@ tsquery_var
        AND (category_filter IS NULL OR ac.category_id = ANY(category_filter))
        AND (tag_filter IS NULL OR t.name = ANY(tag_filter))
        AND (author_filter IS NULL OR a.author_id = ANY(author_filter))
        AND (min_date IS NULL OR a.published_at >= min_date)
        AND (max_date IS NULL OR a.published_at <= max_date)
    )
    SELECT 
        ROW(
        ra.id,
        ra.title,
        ra.subtitle,
        ra.author_name,
        ra.published_at,
        ra.rank,
        ra.highlight
    )::search_result AS results,
    total AS total_count
    FROM ranked_articles ra
    ORDER BY ra.rank DESC
    LIMIT page_size
    OFFSET (page_number - 1) * page_size;
END;
$$ LANGUAGE plpgsql;